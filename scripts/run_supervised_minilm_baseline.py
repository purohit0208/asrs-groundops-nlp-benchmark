#!/usr/bin/env python
"""
Run a supervised MiniLM encoder baseline for record-level ASRS labels.

This script fine-tunes the locally cached
sentence-transformers/all-MiniLM-L6-v2 checkpoint with a classification head.
It loads full ASRS narratives locally for training/evaluation, but writes only
metrics, predictions, and configs. No raw narrative text is exported.
"""

from __future__ import annotations

import copy
import csv
import json
import random
from datetime import date
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from run_record_level_baselines import load_records, read_csv, text_for_row, write_csv


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
OUTPUT_ROOT = ROOT / "outputs" / "baselines" / f"supervised_minilm_{date.today().isoformat()}"

MODEL_REPO_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_LABEL = "supervised_minilm_l6v2_local_finetune"
SEED = 20260603
MAX_LENGTH = 192
BATCH_SIZE = 8
EPOCHS = 2
LEARNING_RATE = 2e-5
WARMUP_RATIO = 0.06

SPLIT_FILES = {
    "train": SPLIT_DIR / "train_records_2026-06-03.csv",
    "dev": SPLIT_DIR / "dev_records_2026-06-03.csv",
    "test": SPLIT_DIR / "test_records_2026-06-03.csv",
}

TASKS = {
    "screening_status": "silver_screening_status",
    "primary_event_type": "silver_primary_event_type",
}

METRIC_FIELDS = ["task", "model", "split", "epoch", "n", "accuracy", "macro_f1", "weighted_f1", "micro_f1"]
PREDICTION_FIELDS = ["task", "model", "split", "corpus_id", "acn", "gold_label", "predicted_label", "correct"]


class TextDataset(Dataset):
    def __init__(self, texts: list[str], label_ids: list[int], tokenizer, max_length: int) -> None:
        self.texts = texts
        self.label_ids = label_ids
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        encoding = self.tokenizer(
            self.texts[index],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.label_ids[index], dtype=torch.long),
        }


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def resolve_model_path() -> str:
    cache_root = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots"
    if cache_root.exists():
        snapshots = sorted([path for path in cache_root.iterdir() if path.is_dir()])
        if snapshots:
            return str(snapshots[-1])
    raise FileNotFoundError(
        "Local all-MiniLM-L6-v2 snapshot not found. Do not download remotely in this script unless the raw-data boundary is revisited."
    )


def build_texts(split_rows: dict[str, list[dict[str, str]]]) -> dict[str, list[str]]:
    records = load_records()
    return {
        split: [text_for_row(row, records) for row in rows]
        for split, rows in split_rows.items()
    }


def labels_for(split_rows: dict[str, list[dict[str, str]]], label_field: str) -> dict[str, list[str]]:
    return {
        split: [row[label_field] for row in rows]
        for split, rows in split_rows.items()
    }


def metrics_row(task: str, split: str, epoch: str, y_true: list[str], y_pred: list[str]) -> dict[str, str]:
    return {
        "task": task,
        "model": MODEL_LABEL,
        "split": split,
        "epoch": epoch,
        "n": str(len(y_true)),
        "accuracy": f"{accuracy_score(y_true, y_pred):.6f}",
        "macro_f1": f"{f1_score(y_true, y_pred, average='macro', zero_division=0):.6f}",
        "weighted_f1": f"{f1_score(y_true, y_pred, average='weighted', zero_division=0):.6f}",
        "micro_f1": f"{f1_score(y_true, y_pred, average='micro', zero_division=0):.6f}",
    }


def prediction_rows(
    task: str,
    split: str,
    rows: list[dict[str, str]],
    y_true: list[str],
    y_pred: list[str],
) -> list[dict[str, str]]:
    output = []
    for row, true_label, pred_label in zip(rows, y_true, y_pred):
        output.append(
            {
                "task": task,
                "model": MODEL_LABEL,
                "split": split,
                "corpus_id": row["corpus_id"],
                "acn": row["acn"],
                "gold_label": true_label,
                "predicted_label": pred_label,
                "correct": str(true_label == pred_label).lower(),
            }
        )
    return output


def make_loader(
    texts: list[str],
    labels: list[str],
    label_to_id: dict[str, int],
    tokenizer,
    shuffle: bool,
) -> DataLoader:
    label_ids = [label_to_id[label] for label in labels]
    dataset = TextDataset(texts, label_ids, tokenizer, MAX_LENGTH)
    generator = torch.Generator()
    generator.manual_seed(SEED)
    return DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=shuffle, generator=generator)


def evaluate(model, loader: DataLoader, id_to_label: dict[int, str], device: torch.device) -> tuple[list[str], list[str], float]:
    model.eval()
    y_true: list[str] = []
    y_pred: list[str] = []
    losses = []
    with torch.no_grad():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            output = model(**batch)
            losses.append(float(output.loss.detach().cpu()))
            pred_ids = torch.argmax(output.logits, dim=-1).detach().cpu().tolist()
            true_ids = batch["labels"].detach().cpu().tolist()
            y_pred.extend(id_to_label[pred_id] for pred_id in pred_ids)
            y_true.extend(id_to_label[true_id] for true_id in true_ids)
    mean_loss = float(np.mean(losses)) if losses else 0.0
    return y_true, y_pred, mean_loss


def write_classification_report(path: Path, task: str, split: str, y_true: list[str], y_pred: list[str]) -> None:
    report = classification_report(y_true, y_pred, zero_division=0)
    labels = sorted(set(y_true) | set(y_pred))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Classification Report: {task} / {MODEL_LABEL} / {split}\n\n")
        f.write("```text\n")
        f.write(report)
        f.write("\n```\n\n")
        f.write("## Confusion Matrix\n\n")
        f.write("| gold \\ predicted | " + " | ".join(labels) + " |\n")
        f.write("|---" + "|---" * len(labels) + "|\n")
        for label, values in zip(labels, matrix):
            f.write("| `" + label + "` | " + " | ".join(str(int(value)) for value in values) + " |\n")


def train_task(
    task: str,
    label_field: str,
    split_rows: dict[str, list[dict[str, str]]],
    split_texts: dict[str, list[str]],
    tokenizer,
    model_path: str,
    device: torch.device,
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    split_labels = labels_for(split_rows, label_field)
    labels = sorted(set(split_labels["train"]) | set(split_labels["dev"]) | set(split_labels["test"]))
    label_to_id = {label: index for index, label in enumerate(labels)}
    id_to_label = {index: label for label, index in label_to_id.items()}

    train_loader = make_loader(split_texts["train"], split_labels["train"], label_to_id, tokenizer, shuffle=True)
    dev_loader = make_loader(split_texts["dev"], split_labels["dev"], label_to_id, tokenizer, shuffle=False)
    test_loader = make_loader(split_texts["test"], split_labels["test"], label_to_id, tokenizer, shuffle=False)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_path,
        num_labels=len(labels),
        id2label={str(index): label for index, label in id_to_label.items()},
        label2id=label_to_id,
        local_files_only=True,
    )
    model.to(device)

    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=np.arange(len(labels)),
        y=np.array([label_to_id[label] for label in split_labels["train"]]),
    )
    class_weights_tensor = torch.tensor(class_weights, dtype=torch.float, device=device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    total_steps = len(train_loader) * EPOCHS
    warmup_steps = max(1, int(total_steps * WARMUP_RATIO))
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

    metrics = []
    best_state = None
    best_epoch = 0
    best_dev_macro = -1.0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            labels_tensor = batch.pop("labels")
            optimizer.zero_grad(set_to_none=True)
            output = model(**batch)
            loss = torch.nn.functional.cross_entropy(output.logits, labels_tensor, weight=class_weights_tensor)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

        dev_true, dev_pred, _ = evaluate(model, dev_loader, id_to_label, device)
        dev_row = metrics_row(task, "dev", str(epoch), dev_true, dev_pred)
        metrics.append(dev_row)
        dev_macro = float(dev_row["macro_f1"])
        print(f"{task} epoch={epoch} dev_macro_f1={dev_macro:.6f}")
        if dev_macro > best_dev_macro:
            best_dev_macro = dev_macro
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())

    if best_state is not None:
        model.load_state_dict(best_state)

    output_metrics = []
    predictions = []
    for split, loader in [("dev", dev_loader), ("test", test_loader)]:
        y_true, y_pred, _ = evaluate(model, loader, id_to_label, device)
        output_metrics.append(metrics_row(task, split, f"best_dev_epoch_{best_epoch}", y_true, y_pred))
        if split == "test":
            predictions.extend(prediction_rows(task, split, split_rows[split], y_true, y_pred))
        write_classification_report(
            OUTPUT_ROOT / f"classification_report_{task}_{MODEL_LABEL}_{split}.md",
            task,
            split,
            y_true,
            y_pred,
        )

    training_trace_path = OUTPUT_ROOT / f"training_trace_{task}.csv"
    write_csv(training_trace_path, metrics, METRIC_FIELDS)
    task_config = {
        "labels": labels,
        "label_to_id": label_to_id,
        "best_epoch": best_epoch,
        "best_dev_macro_f1": best_dev_macro,
        "class_weights": {label: float(class_weights[label_to_id[label]]) for label in labels},
    }
    return output_metrics, predictions, task_config


def write_summary(metrics: list[dict[str, str]]) -> None:
    summary_path = OUTPUT_ROOT / "supervised_minilm_baseline_summary.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Supervised MiniLM Baseline Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This is a local CPU fine-tuning baseline using the cached `sentence-transformers/all-MiniLM-L6-v2` checkpoint with a classification head. Full raw ASRS narratives are loaded locally and are not written to output files. No Hugging Face remote job, hosted inference call, or paid API is used.\n\n")
        f.write("## Metrics\n\n")
        f.write("| task | model | split | epoch | n | accuracy | macro_f1 | weighted_f1 | micro_f1 |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in metrics:
            f.write(
                f"| `{row['task']}` | `{row['model']}` | `{row['split']}` | `{row['epoch']}` | {row['n']} | {row['accuracy']} | {row['macro_f1']} | {row['weighted_f1']} | {row['micro_f1']} |\n"
            )
        f.write("\n## Interpretation\n\n")
        f.write("- Treat this as the first supervised encoder baseline, not as a final multi-seed transformer study.\n")
        f.write("- Compare against TF-IDF LinearSVC before deciding whether additional GPU/multi-seed fine-tuning is justified.\n")
        f.write("- Do not interpret record-level scores as full event-mention extraction performance.\n")


def main() -> None:
    set_seed(SEED)
    torch.set_num_threads(max(1, min(8, torch.get_num_threads())))
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    model_path = resolve_model_path()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}")
    print(f"model_path={model_path}")

    split_rows = {split: read_csv(path) for split, path in SPLIT_FILES.items()}
    split_texts = build_texts(split_rows)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)

    all_metrics = []
    all_predictions = []
    task_configs = {}

    for task, label_field in TASKS.items():
        metrics, predictions, task_config = train_task(
            task,
            label_field,
            split_rows,
            split_texts,
            tokenizer,
            model_path,
            device,
        )
        all_metrics.extend(metrics)
        all_predictions.extend(predictions)
        task_configs[task] = task_config

    write_csv(OUTPUT_ROOT / "supervised_minilm_baseline_metrics.csv", all_metrics, METRIC_FIELDS)
    write_csv(OUTPUT_ROOT / "supervised_minilm_baseline_predictions.csv", all_predictions, PREDICTION_FIELDS)
    config = {
        "created": date.today().isoformat(),
        "model_repo_id": MODEL_REPO_ID,
        "model_path_used": model_path,
        "model_label": MODEL_LABEL,
        "seed": SEED,
        "max_length": MAX_LENGTH,
        "batch_size": BATCH_SIZE,
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "warmup_ratio": WARMUP_RATIO,
        "device": str(device),
        "tasks": TASKS,
        "split_files": {key: str(value) for key, value in SPLIT_FILES.items()},
        "task_configs": task_configs,
        "boundary": "Full raw ASRS narratives are loaded locally and not written to outputs. No remote HF job or hosted inference is used.",
    }
    (OUTPUT_ROOT / "supervised_minilm_baseline_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_summary(all_metrics)

    print(f"output_dir={OUTPUT_ROOT}")
    print(f"metrics={OUTPUT_ROOT / 'supervised_minilm_baseline_metrics.csv'}")
    for row in all_metrics:
        if row["split"] == "test":
            print(row)


if __name__ == "__main__":
    main()
