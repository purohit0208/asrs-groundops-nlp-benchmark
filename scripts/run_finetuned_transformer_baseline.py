#!/usr/bin/env python
"""Fine-tuned transformer baseline for the ASRS GroundOps record-level corpus.

Adds the fine-tuned encoder baseline (DistilBERT/RoBERTa/Longformer) that the
MDPI MAKE editor and ADVEI Reviewer #3 said was missing. Consistent with
run_supervised_minilm_baseline.py. Multi-seed, class-weighted, dev-selected,
with 1,000-sample bootstrap 95% CIs. Raw ASRS text is loaded locally and never
written to outputs; only public model weights are downloaded.
"""

from __future__ import annotations

import argparse
import copy
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

SPLIT_SETS = {
    "expanded8800": {
        "train": SPLIT_DIR / "expanded_8800_reference_eval_train_records_2026-06-04.csv",
        "dev": SPLIT_DIR / "expanded_8800_reference_eval_dev_records_2026-06-04.csv",
        "test": SPLIT_DIR / "expanded_8800_reference_eval_test_records_2026-06-04.csv",
    },
    "seed5000": {
        "train": SPLIT_DIR / "train_records_2026-06-04.csv",
        "dev": SPLIT_DIR / "dev_records_2026-06-04.csv",
        "test": SPLIT_DIR / "test_records_2026-06-04.csv",
    },
}

TASKS = {
    "screening_status": "silver_screening_status",
    "primary_event_type": "silver_primary_event_type",
}

COARSE_PRIMARY = {
    "not_relevant": "not_relevant",
    "hazmat_mobility_device": "hazmat_mobility_device",
    "maintenance_readiness": "maintenance_readiness",
    "baggage_cargo_weight_balance": "baggage_cargo",
    "cabin_service": "cabin_gate_passenger",
    "gate_or_boarding": "cabin_gate_passenger",
    "jetway_or_gate_infrastructure": "cabin_gate_passenger",
    "pushback_towing_chocks": "ramp_servicing",
    "ramp_ground_handling": "ramp_servicing",
    "other_ground_operation": "ramp_servicing",
    "fueling": "ramp_servicing",
    "dispatch_or_coordination": "ramp_servicing",
}

METRIC_FIELDS = [
    "task", "model", "split", "seed", "n",
    "accuracy", "macro_f1", "weighted_f1", "micro_f1",
    "macro_f1_ci_low", "macro_f1_ci_high", "accuracy_ci_low", "accuracy_ci_high",
]
AGG_FIELDS = [
    "task", "model", "split", "n_seeds", "n",
    "accuracy_mean", "accuracy_std", "macro_f1_mean", "macro_f1_std",
    "micro_f1_mean", "micro_f1_std", "weighted_f1_mean", "weighted_f1_std",
]
PREDICTION_FIELDS = ["task", "model", "seed", "split", "corpus_id", "acn", "gold_label", "predicted_label", "correct"]

BOOTSTRAP_SAMPLES = 1000
BOOTSTRAP_SEED = 20260619


class TextDataset(Dataset):
    def __init__(self, texts, label_ids, tokenizer, max_length):
        self.texts = texts
        self.label_ids = label_ids
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, index):
        enc = self.tokenizer(
            self.texts[index], truncation=True, padding="max_length",
            max_length=self.max_length, return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.label_ids[index], dtype=torch.long),
        }


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def bootstrap_ci(y_true, y_pred, metric_fn, n_samples=BOOTSTRAP_SAMPLES, seed=BOOTSTRAP_SEED):
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true, dtype=object)
    y_pred = np.asarray(y_pred, dtype=object)
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0
    stats = []
    for _ in range(n_samples):
        idx = rng.integers(0, n, n)
        stats.append(metric_fn(list(y_true[idx]), list(y_pred[idx])))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def macro_f1(y_true, y_pred):
    return f1_score(y_true, y_pred, average="macro", zero_division=0)


def acc_metric(y_true, y_pred):
    return accuracy_score(y_true, y_pred)


def metrics_row(task, model_label, split, seed, y_true, y_pred):
    mf_low, mf_high = bootstrap_ci(y_true, y_pred, macro_f1)
    ac_low, ac_high = bootstrap_ci(y_true, y_pred, acc_metric)
    return {
        "task": task, "model": model_label, "split": split, "seed": str(seed),
        "n": str(len(y_true)),
        "accuracy": f"{accuracy_score(y_true, y_pred):.6f}",
        "macro_f1": f"{f1_score(y_true, y_pred, average='macro', zero_division=0):.6f}",
        "weighted_f1": f"{f1_score(y_true, y_pred, average='weighted', zero_division=0):.6f}",
        "micro_f1": f"{f1_score(y_true, y_pred, average='micro', zero_division=0):.6f}",
        "macro_f1_ci_low": f"{mf_low:.6f}", "macro_f1_ci_high": f"{mf_high:.6f}",
        "accuracy_ci_low": f"{ac_low:.6f}", "accuracy_ci_high": f"{ac_high:.6f}",
    }


def prediction_rows(task, model_label, seed, split, rows, y_true, y_pred):
    out = []
    for row, t, p in zip(rows, y_true, y_pred):
        out.append({
            "task": task, "model": model_label, "seed": str(seed), "split": split,
            "corpus_id": row["corpus_id"], "acn": row["acn"],
            "gold_label": t, "predicted_label": p, "correct": str(t == p).lower(),
        })
    return out


def write_classification_report(path, task, model_label, split, seed, y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    lines = [f"# Classification Report: {task} / {model_label} / {split} / seed {seed}", "", "```text",
             classification_report(y_true, y_pred, zero_division=0), "```", "", "## Confusion Matrix", "",
             "| gold | " + " | ".join(labels) + " |", "|---" + "|---" * len(labels) + "|"]
    for label, values in zip(labels, matrix):
        lines.append("| `" + label + "` | " + " | ".join(str(int(v)) for v in values) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_texts(split_rows):
    records = load_records()
    return {split: [text_for_row(row, records) for row in rows] for split, rows in split_rows.items()}


def make_loader(texts, label_ids, tokenizer, max_length, batch_size, shuffle, seed):
    dataset = TextDataset(texts, label_ids, tokenizer, max_length)
    gen = torch.Generator()
    gen.manual_seed(seed)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, generator=gen)


def evaluate(model, loader, id_to_label, device):
    model.eval()
    y_pred, y_true = [], []
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
            pred_ids = torch.argmax(logits, dim=-1).detach().cpu().tolist()
            true_ids = batch["labels"].detach().cpu().tolist()
            y_pred.extend(id_to_label[i] for i in pred_ids)
            y_true.extend(id_to_label[i] for i in true_ids)
    return y_true, y_pred


def train_one(task, label_field, split_rows, split_texts, args, seed, device):
    split_labels = {s: [r[label_field] for r in rows] for s, rows in split_rows.items()}
    if args.coarse and task == "primary_event_type":
        split_labels = {s: [COARSE_PRIMARY.get(l, l) for l in labs] for s, labs in split_labels.items()}
    labels = sorted(set(split_labels["train"]) | set(split_labels["dev"]) | set(split_labels["test"]))
    label_to_id = {l: i for i, l in enumerate(labels)}
    id_to_label = {i: l for l, i in label_to_id.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=args.local_files_only, use_fast=True)
    added_pad = False
    if tokenizer.pad_token is None:
        if tokenizer.eos_token is not None:
            tokenizer.pad_token = tokenizer.eos_token
        else:
            tokenizer.add_special_tokens({"pad_token": "[PAD]"})
            added_pad = True
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(labels),
        id2label={str(i): l for i, l in id_to_label.items()}, label2id=label_to_id,
        local_files_only=args.local_files_only,
    ).to(device)
    if added_pad:
        model.resize_token_embeddings(len(tokenizer))

    def ids(split):
        return [label_to_id[l] for l in split_labels[split]]

    train_loader = make_loader(split_texts["train"], ids("train"), tokenizer, args.max_length, args.batch_size, True, seed)
    dev_loader = make_loader(split_texts["dev"], ids("dev"), tokenizer, args.max_length, args.eval_batch_size, False, seed)
    test_loader = make_loader(split_texts["test"], ids("test"), tokenizer, args.max_length, args.eval_batch_size, False, seed)

    y_train_ids = np.array(ids("train"))
    present = np.unique(y_train_ids)
    present_weights = compute_class_weight("balanced", classes=present, y=y_train_ids)
    full_weights = np.ones(len(labels), dtype=float)
    for cls_id, w in zip(present, present_weights):
        full_weights[int(cls_id)] = w
    cw = torch.tensor(full_weights, dtype=torch.float, device=device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    total_steps = max(1, len(train_loader) * args.epochs)
    scheduler = get_linear_schedule_with_warmup(optimizer, int(total_steps * args.warmup_ratio), total_steps)
    use_amp = bool(args.fp16 and device.type == "cuda")
    scaler = torch.amp.GradScaler('cuda', enabled=use_amp)

    best_state, best_dev, best_epoch = None, -1.0, 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            labels_t = batch.pop("labels")
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast('cuda', enabled=use_amp):
                logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
                loss = torch.nn.functional.cross_entropy(logits, labels_t, weight=cw)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
        dev_true, dev_pred = evaluate(model, dev_loader, id_to_label, device)
        dev_macro = f1_score(dev_true, dev_pred, average="macro", zero_division=0)
        print(f"  [{task}] seed={seed} epoch={epoch} dev_macro_f1={dev_macro:.4f}")
        if dev_macro > best_dev:
            best_dev, best_epoch = dev_macro, epoch
            best_state = copy.deepcopy(model.state_dict())

    if best_state is not None:
        model.load_state_dict(best_state)

    results = {}
    for split, loader in [("dev", dev_loader), ("test", test_loader)]:
        results[split] = evaluate(model, loader, id_to_label, device)
    return results, best_epoch, labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="distilbert-base-uncased")
    parser.add_argument("--split-set", default="expanded8800", choices=list(SPLIT_SETS))
    parser.add_argument("--seeds", default="20260619,20260620,20260621")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--eval-batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=320)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--warmup-ratio", type=float, default=0.06)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--coarse", action="store_true", help="remap primary_event_type to 6-class coarse scheme")
    parser.add_argument("--limit-train", type=int, default=None)
    parser.add_argument("--limit-eval", type=int, default=None)
    args = parser.parse_args()

    if args.smoke_test:
        args.model = "prajjwal1/bert-tiny"
        args.seeds = "1"
        args.epochs = 1
        args.batch_size = 8
        args.max_length = 64
        if args.limit_train is None:
            args.limit_train = 120
        if args.limit_eval is None:
            args.limit_eval = 60

    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    sfx = "_coarse" if args.coarse else ""
    model_label = f"finetuned_{args.model.split('/')[-1].replace('-', '_')}{sfx}"
    out_dir = ROOT / "outputs" / "baselines" / f"finetuned_transformer_{args.model.split('/')[-1]}{sfx}_{date.today().isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)

    torch.set_num_threads(max(1, min(8, torch.get_num_threads())))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}  model={args.model}  split_set={args.split_set}  seeds={seeds}")

    split_files = SPLIT_SETS[args.split_set]
    split_rows = {s: read_csv(p) for s, p in split_files.items()}
    if args.limit_train is not None:
        split_rows["train"] = split_rows["train"][: args.limit_train]
    if args.limit_eval is not None:
        split_rows["dev"] = split_rows["dev"][: args.limit_eval]
        split_rows["test"] = split_rows["test"][: args.limit_eval]

    split_texts = build_texts(split_rows)
    all_metrics, all_aggregates, all_predictions = [], [], []
    per_seed = {task: {"dev": [], "test": []} for task in TASKS}

    for task, label_field in TASKS.items():
        wrote_predictions = False
        for seed in seeds:
            set_seed(seed)
            results, best_epoch, labels = train_one(task, label_field, split_rows, split_texts, args, seed, device)
            for split in ["dev", "test"]:
                y_true, y_pred = results[split]
                row = metrics_row(task, model_label, split, seed, y_true, y_pred)
                all_metrics.append(row)
                per_seed[task][split].append(row)
            if not wrote_predictions:
                t_true, t_pred = results["test"]
                all_predictions.extend(prediction_rows(task, model_label, seed, "test", split_rows["test"], t_true, t_pred))
                write_classification_report(out_dir / f"classification_report_{task}_{model_label}_test_seed{seed}.md",
                                            task, model_label, "test", seed, t_true, t_pred)
                wrote_predictions = True

        for split in ["dev", "test"]:
            rows = per_seed[task][split]

            def col(name):
                return np.array([float(r[name]) for r in rows])

            all_aggregates.append({
                "task": task, "model": model_label, "split": split,
                "n_seeds": str(len(rows)), "n": rows[0]["n"],
                "accuracy_mean": f"{col('accuracy').mean():.6f}", "accuracy_std": f"{col('accuracy').std(ddof=0):.6f}",
                "macro_f1_mean": f"{col('macro_f1').mean():.6f}", "macro_f1_std": f"{col('macro_f1').std(ddof=0):.6f}",
                "micro_f1_mean": f"{col('micro_f1').mean():.6f}", "micro_f1_std": f"{col('micro_f1').std(ddof=0):.6f}",
                "weighted_f1_mean": f"{col('weighted_f1').mean():.6f}", "weighted_f1_std": f"{col('weighted_f1').std(ddof=0):.6f}",
            })

    write_csv(out_dir / "finetuned_transformer_metrics.csv", all_metrics, METRIC_FIELDS)
    write_csv(out_dir / "finetuned_transformer_aggregate.csv", all_aggregates, AGG_FIELDS)
    write_csv(out_dir / "finetuned_transformer_predictions.csv", all_predictions, PREDICTION_FIELDS)

    config = {
        "created": date.today().isoformat(), "model": args.model, "model_label": model_label,
        "split_set": args.split_set, "split_files": {k: str(v) for k, v in split_files.items()},
        "seeds": seeds, "epochs": args.epochs, "batch_size": args.batch_size, "max_length": args.max_length,
        "learning_rate": args.learning_rate, "warmup_ratio": args.warmup_ratio, "fp16": args.fp16,
        "device": str(device), "tasks": TASKS, "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "boundary": "Raw ASRS text loaded locally and never written to outputs. Only public model weights are downloaded.",
        "smoke_test": args.smoke_test,
    }
    (out_dir / "finetuned_transformer_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    s = ["# Fine-Tuned Transformer Baseline Summary", "", f"Created: {date.today().isoformat()}", "",
         f"Model: `{args.model}` | Split: `{args.split_set}` | Seeds: {seeds} | Device: `{device}`", "",
         "## Boundary", "",
         "- Local fine-tuning. Raw ASRS narratives loaded locally and never written to outputs; only public model weights downloaded.",
         "- Train = verified seed train + 3,800 agent-silver weak-label rows. Dev/test = author-verified reference rows only.",
         "- DistilBERT/RoBERTa truncate at 512 word-pieces; use Longformer for long narratives.", "",
         "## Aggregate test results (mean +/- std over seeds)", "",
         "| task | model | split | n_seeds | n | accuracy | macro_f1 | micro_f1 |",
         "|---|---|---|---:|---:|---|---|---|"]
    for r in all_aggregates:
        if r["split"] == "test":
            s.append(f"| `{r['task']}` | `{r['model']}` | {r['split']} | {r['n_seeds']} | {r['n']} | "
                     f"{r['accuracy_mean']}+/-{r['accuracy_std']} | {r['macro_f1_mean']}+/-{r['macro_f1_std']} | "
                     f"{r['micro_f1_mean']}+/-{r['micro_f1_std']} |")
    s += ["", "## Interpretation", "",
          "- Compare test macro_f1 against TF-IDF LinearSVC (current best) and supervised MiniLM.",
          "- Report mean +/- std over seeds and the per-seed 1,000-sample bootstrap 95% CIs (metrics CSV).",
          "- If the encoder does not beat TF-IDF, report that honestly as a benchmark finding."]
    (out_dir / "finetuned_transformer_summary.md").write_text("\n".join(s) + "\n", encoding="utf-8")

    print(f"output_dir={out_dir}")
    for r in all_aggregates:
        if r["split"] == "test":
            print(r)


if __name__ == "__main__":
    main()
