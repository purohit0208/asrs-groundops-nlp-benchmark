#!/usr/bin/env python
"""
Run a bounded Hugging Face Qwen structured-output baseline for ASRS records.

This script sends raw ASRS text to Hugging Face Inference Providers. It requires
the explicit data-boundary approval recorded in:
protocols/EXPANDED_8800_CORPUS_AND_REMOTE_LLM_DECISION.md

Safety defaults:
- reads HF_TOKEN from the environment;
- does not write raw prompts, raw ASRS text, or raw model responses;
- writes parsed label predictions, validity flags, timings, and cost estimates;
- resumes from an existing prediction CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any

import requests
from sklearn.metrics import accuracy_score, f1_score

from run_record_level_baselines import load_records, read_csv, text_for_row, write_csv


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
OUTPUT_ROOT = ROOT / "outputs" / "baselines" / f"hf_qwen_structured_{date.today().isoformat()}"
ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

DEFAULT_SPLIT_FILE = SPLIT_DIR / "expanded_8800_reference_eval_test_records_2026-06-04.csv"
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct:cheapest"
BASE_MODEL_FOR_REPORT = "Qwen/Qwen2.5-7B-Instruct"

SCREENING_LABELS = [
    "include_ground_cabin_event",
    "exclude_not_ground_or_cabin",
    "uncertain_needs_review",
]

EVENT_LABELS = [
    "cabin_service",
    "passenger_assistance",
    "gate_or_boarding",
    "ramp_ground_handling",
    "pushback_towing_chocks",
    "baggage_cargo_weight_balance",
    "fueling",
    "maintenance_readiness",
    "dispatch_or_coordination",
    "jetway_or_gate_infrastructure",
    "hazmat_mobility_device",
    "other_ground_operation",
    "not_relevant",
]

PREDICTION_FIELDS = [
    "run_date",
    "model",
    "split_file",
    "row_index",
    "corpus_id",
    "acn",
    "gold_screening_status",
    "gold_primary_event_type",
    "llm_screening_status",
    "llm_primary_event_type",
    "llm_secondary_event_types",
    "llm_possible_multi_event",
    "llm_confidence",
    "valid_json",
    "schema_valid",
    "error_type",
    "latency_seconds",
    "approx_input_tokens",
    "approx_output_tokens",
    "estimated_cost_usd",
]

METRIC_FIELDS = [
    "run_date",
    "model",
    "split_file",
    "completed_rows",
    "valid_json_rows",
    "schema_valid_rows",
    "task",
    "accuracy",
    "macro_f1",
    "weighted_f1",
    "estimated_total_cost_usd",
]

PRINT_LOCK = threading.Lock()

PRICE_BY_MODEL_PREFIX = {
    # Hugging Face router metadata checked on 2026-06-04.
    "Qwen/Qwen2.5-7B-Instruct": (0.30, 0.30),
    "Qwen/Qwen2.5-72B-Instruct": (0.38, 0.40),
    "Qwen/Qwen3-32B": (0.08, 0.25),
}


def approx_tokens(value: str) -> int:
    return max(1, round(len(value) / 4))


def prompt_for(text: str) -> list[dict[str, str]]:
    system = (
        "You label NASA ASRS aviation safety reports for a research benchmark. "
        "Return only valid minified JSON. Do not quote or copy source text. "
        "If the report is not about ground operations or cabin service, use not_relevant."
    )
    user = {
        "task": "Classify the ASRS report at record level.",
        "allowed_screening_status": SCREENING_LABELS,
        "allowed_event_types": EVENT_LABELS,
        "output_schema": {
            "screening_status": "one allowed screening label",
            "primary_event_type": "one allowed event label",
            "secondary_event_types": "array of allowed event labels, excluding primary unless no secondary labels",
            "possible_multi_event": "boolean",
            "confidence": "low, medium, or high",
        },
        "rules": [
            "Use include_ground_cabin_event only for gate, boarding/deboarding, cabin readiness/service, ramp, pushback/towing/chocks, baggage/cargo/load sheet, fueling, maintenance readiness at gate/ramp, dispatch/operations coordination tied to ground readiness, jetway/gate infrastructure, or mobility-device hazmat handling.",
            "Use exclude_not_ground_or_cabin and primary_event_type not_relevant for airborne, en-route, approach, weather, ATC, or cockpit-only reports without ground/cabin operational relevance.",
            "Use uncertain_needs_review only when the evidence is genuinely ambiguous.",
            "Do not include explanations outside JSON.",
        ],
        "asrs_report": text,
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=True)},
    ]


def extract_json_object(value: str) -> dict[str, Any]:
    value = value.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?", "", value).strip()
        value = re.sub(r"```$", "", value).strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(value[start : end + 1])
    if not isinstance(parsed, dict):
        raise TypeError("Parsed JSON is not an object")
    return parsed


def clean_prediction(parsed: dict[str, Any]) -> tuple[dict[str, str], bool]:
    screening = str(parsed.get("screening_status", "")).strip()
    primary = str(parsed.get("primary_event_type", "")).strip()
    secondary_raw = parsed.get("secondary_event_types", [])
    if not isinstance(secondary_raw, list):
        secondary_raw = []
    secondary = [str(item).strip() for item in secondary_raw if str(item).strip()]
    possible_multi = parsed.get("possible_multi_event", False)
    confidence = str(parsed.get("confidence", "")).strip().lower()

    schema_valid = True
    if screening not in SCREENING_LABELS:
        schema_valid = False
    if primary not in EVENT_LABELS:
        schema_valid = False
    if any(label not in EVENT_LABELS for label in secondary):
        schema_valid = False
    if confidence not in {"low", "medium", "high"}:
        schema_valid = False
    if not isinstance(possible_multi, bool):
        schema_valid = False

    if not schema_valid:
        screening = screening if screening in SCREENING_LABELS else "uncertain_needs_review"
        primary = primary if primary in EVENT_LABELS else "not_relevant"
        secondary = [label for label in secondary if label in EVENT_LABELS]
        confidence = confidence if confidence in {"low", "medium", "high"} else "low"
        possible_multi = bool(possible_multi) if isinstance(possible_multi, bool) else False

    return (
        {
            "llm_screening_status": screening,
            "llm_primary_event_type": primary,
            "llm_secondary_event_types": ";".join(dict.fromkeys(secondary)),
            "llm_possible_multi_event": str(possible_multi).lower(),
            "llm_confidence": confidence,
        },
        schema_valid,
    )


def call_hf(messages: list[dict[str, str]], model: str, token: str, timeout: int, max_retries: int) -> tuple[str, float]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 180,
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    last_error = None
    for attempt in range(max_retries + 1):
        start = time.perf_counter()
        try:
            response = requests.post(ROUTER_URL, headers=headers, json=payload, timeout=timeout)
            latency = time.perf_counter() - start
            if response.status_code in {429, 500, 502, 503, 504} and attempt < max_retries:
                time.sleep(min(30, 2 ** attempt))
                continue
            response.raise_for_status()
            data = response.json()
            return normalize_message_content(data["choices"][0]["message"].get("content", "")), latency
        except Exception as exc:  # noqa: BLE001 - keep retry boundary simple for batch jobs.
            last_error = exc
            if attempt < max_retries:
                time.sleep(min(30, 2 ** attempt))
                continue
    raise RuntimeError(str(last_error))


def normalize_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        return "\n".join(parts)
    return str(content)


def price_for_model(model: str) -> tuple[float, float]:
    base = model.split(":", 1)[0]
    return PRICE_BY_MODEL_PREFIX.get(base, (0.30, 0.30))


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    input_price, output_price = price_for_model(model)
    return (input_tokens / 1_000_000) * input_price + (output_tokens / 1_000_000) * output_price


def process_row(args: tuple[int, dict[str, str], dict[str, dict], argparse.Namespace, str | None]) -> dict[str, str]:
    row_index, row, records, parsed_args, token = args
    text = text_for_row(row, records)
    messages = prompt_for(text)
    prompt_text_for_estimate = json.dumps(messages, ensure_ascii=True)
    input_tokens = approx_tokens(prompt_text_for_estimate)

    base = {
        "run_date": date.today().isoformat(),
        "model": parsed_args.model,
        "split_file": str(parsed_args.split_file),
        "row_index": str(row_index),
        "corpus_id": row["corpus_id"],
        "acn": row["acn"],
        "gold_screening_status": row["silver_screening_status"],
        "gold_primary_event_type": row["silver_primary_event_type"],
        "llm_screening_status": "",
        "llm_primary_event_type": "",
        "llm_secondary_event_types": "",
        "llm_possible_multi_event": "",
        "llm_confidence": "",
        "valid_json": "false",
        "schema_valid": "false",
        "error_type": "",
        "latency_seconds": "",
        "approx_input_tokens": str(input_tokens),
        "approx_output_tokens": "0",
        "estimated_cost_usd": "0.000000",
    }

    if parsed_args.estimate_only:
        base["error_type"] = "estimate_only"
        base["estimated_cost_usd"] = f"{estimate_cost(input_tokens, 120, parsed_args.model):.6f}"
        return base

    if not token:
        base["error_type"] = "missing_hf_token"
        return base

    try:
        content, latency = call_hf(messages, parsed_args.model, token, parsed_args.timeout, parsed_args.max_retries)
        output_tokens = approx_tokens(content)
        parsed = extract_json_object(content)
        cleaned, schema_valid = clean_prediction(parsed)
        base.update(cleaned)
        base["valid_json"] = "true"
        base["schema_valid"] = str(schema_valid).lower()
        base["latency_seconds"] = f"{latency:.3f}"
        base["approx_output_tokens"] = str(output_tokens)
        base["estimated_cost_usd"] = f"{estimate_cost(input_tokens, output_tokens, parsed_args.model):.6f}"
    except Exception as exc:  # noqa: BLE001
        base["error_type"] = type(exc).__name__
    return base


def read_existing(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {row["acn"]: row for row in csv.DictReader(f)}


def append_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PREDICTION_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def write_metrics(output_dir: Path, prediction_rows: list[dict[str, str]], split_file: Path, model: str) -> None:
    completed = [row for row in prediction_rows if row["valid_json"] == "true"]
    schema_valid = [row for row in completed if row["schema_valid"] == "true"]
    total_cost = sum(float(row["estimated_cost_usd"] or 0) for row in prediction_rows)
    metrics = []
    for task, gold_field, pred_field in [
        ("screening_status", "gold_screening_status", "llm_screening_status"),
        ("primary_event_type", "gold_primary_event_type", "llm_primary_event_type"),
    ]:
        eval_rows = [row for row in schema_valid if row[pred_field]]
        if not eval_rows:
            accuracy = macro_f1 = weighted_f1 = 0.0
        else:
            y_true = [row[gold_field] for row in eval_rows]
            y_pred = [row[pred_field] for row in eval_rows]
            accuracy = accuracy_score(y_true, y_pred)
            macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
            weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
        metrics.append(
            {
                "run_date": date.today().isoformat(),
                "model": model,
                "split_file": str(split_file),
                "completed_rows": str(len(prediction_rows)),
                "valid_json_rows": str(len(completed)),
                "schema_valid_rows": str(len(schema_valid)),
                "task": task,
                "accuracy": f"{accuracy:.6f}",
                "macro_f1": f"{macro_f1:.6f}",
                "weighted_f1": f"{weighted_f1:.6f}",
                "estimated_total_cost_usd": f"{total_cost:.6f}",
            }
        )
    write_csv(output_dir / "hf_qwen_structured_metrics.csv", metrics, METRIC_FIELDS)

    with (output_dir / "hf_qwen_structured_summary.md").open("w", encoding="utf-8") as f:
        f.write("# Hugging Face Qwen Structured Baseline Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This run sends raw ASRS text to Hugging Face Inference Providers under the approval recorded in `protocols/EXPANDED_8800_CORPUS_AND_REMOTE_LLM_DECISION.md`. Output files do not store raw prompts, raw ASRS text, or raw model responses.\n\n")
        f.write(f"- Model: `{model}`\n")
        f.write(f"- Base model for report: `{BASE_MODEL_FOR_REPORT}`\n")
        f.write(f"- Split file: `{split_file}`\n")
        f.write(f"- Completed rows in prediction file: {len(prediction_rows)}\n")
        f.write(f"- Valid JSON rows: {len(completed)}\n")
        f.write(f"- Schema-valid rows: {len(schema_valid)}\n")
        f.write(f"- Estimated total token cost: ${total_cost:.6f}\n\n")
        f.write("## Metrics On Schema-Valid Rows\n\n")
        f.write("| task | accuracy | macro_f1 | weighted_f1 |\n")
        f.write("|---|---:|---:|---:|\n")
        for row in metrics:
            f.write(f"| `{row['task']}` | {row['accuracy']} | {row['macro_f1']} | {row['weighted_f1']} |\n")
        f.write("\n## Reproducibility Note\n\n")
        f.write("Use `--limit` for smoke tests and rerun without `--limit` to complete the selected split. The script resumes from the existing prediction CSV by ACN.\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HF Qwen structured ASRS baseline")
    parser.add_argument("--split-file", type=Path, default=DEFAULT_SPLIT_FILE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum number of new rows to process")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--estimate-only", action="store_true", help="Estimate token cost without remote calls")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = args.output_dir / "hf_qwen_structured_predictions.csv"

    rows = read_csv(args.split_file)
    existing = read_existing(predictions_path)
    rows_to_process = [(i, row) for i, row in enumerate(rows, start=1) if row["acn"] not in existing]
    if args.limit is not None:
        rows_to_process = rows_to_process[: args.limit]

    records = load_records()
    token = os.environ.get("HF_TOKEN")
    if not token and not args.estimate_only:
        raise SystemExit("HF_TOKEN environment variable is required unless --estimate-only is used.")

    print(f"split_file={args.split_file}")
    print(f"output_dir={args.output_dir}")
    print(f"existing_predictions={len(existing)}")
    print(f"new_rows_to_process={len(rows_to_process)}")
    print(f"workers={args.workers}")
    print(f"estimate_only={args.estimate_only}")

    completed_rows: list[dict[str, str]] = []
    if rows_to_process:
        work_items = [(i, row, records, args, token) for i, row in rows_to_process]
        if args.workers <= 1:
            for item in work_items:
                result = process_row(item)
                append_rows(predictions_path, [result])
                completed_rows.append(result)
                with PRINT_LOCK:
                    print(f"processed={len(completed_rows)}/{len(work_items)} acn={result['acn']} valid_json={result['valid_json']} schema_valid={result['schema_valid']} error={result['error_type']}")
        else:
            batch_buffer: list[dict[str, str]] = []
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(process_row, item) for item in work_items]
                for future in as_completed(futures):
                    result = future.result()
                    batch_buffer.append(result)
                    completed_rows.append(result)
                    with PRINT_LOCK:
                        print(f"processed={len(completed_rows)}/{len(work_items)} acn={result['acn']} valid_json={result['valid_json']} schema_valid={result['schema_valid']} error={result['error_type']}")
                    if len(batch_buffer) >= 10:
                        append_rows(predictions_path, batch_buffer)
                        batch_buffer = []
                if batch_buffer:
                    append_rows(predictions_path, batch_buffer)

    all_predictions = list(read_existing(predictions_path).values())
    write_metrics(args.output_dir, all_predictions, args.split_file, args.model)
    print(f"predictions={predictions_path}")
    print(f"metrics={args.output_dir / 'hf_qwen_structured_metrics.csv'}")
    print(f"summary={args.output_dir / 'hf_qwen_structured_summary.md'}")


if __name__ == "__main__":
    main()
