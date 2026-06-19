#!/usr/bin/env python
"""
Inter-annotator agreement (IAA) worksheet builder + scorer for the ASRS GroundOps benchmark.

WHY: the corpus labels are agent-silver + single-author-verified, with no measured
inter-annotator agreement. A second independent annotator on a stratified sample of
the verified TEST set lets us report Cohen's kappa and turn "single-reviewer silver
labels" into "labels with measured agreement" - the main label-quality fix.

MODES
  --make   : build a BLIND worksheet (narratives + empty label columns) from a
             stratified sample of the test split, plus a hidden answer key and the
             allowed-label list. The worksheet contains NO existing labels.
  --score  : compare a FILLED worksheet against the hidden key; report Cohen's kappa,
             percent agreement, and n for screening_status and primary_event_type.

The worksheet contains raw ASRS narratives -> keep it LOCAL; do not commit it to the
public repo.
"""
from __future__ import annotations
import argparse, csv, random
from collections import defaultdict
from datetime import date
from pathlib import Path

from sklearn.metrics import cohen_kappa_score
from run_record_level_baselines import load_records, read_csv, text_for_row, write_csv

ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
OUT_DIR = ROOT / "annotation" / f"iaa_{date.today().isoformat()}"
TEST_SPLIT = SPLIT_DIR / "expanded_8800_reference_eval_test_records_2026-06-04.csv"
SCREEN = "silver_screening_status"
PRIMARY = "silver_primary_event_type"


def make(sample_size: int, seed: int) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(TEST_SPLIT)
    records = load_records()

    # stratify by primary_event_type, proportional, >=1 per class, deterministic
    by_cls = defaultdict(list)
    for r in rows:
        by_cls[r[PRIMARY]].append(r)
    rng = random.Random(seed)
    selected = []
    for cls, items in by_cls.items():
        rng.shuffle(items)
        k = max(1, round(sample_size * len(items) / len(rows)))
        selected.extend(items[:k])
    rng.shuffle(selected)
    selected = selected[:sample_size]

    work = [{"corpus_id": r["corpus_id"], "acn": r["acn"],
             "narrative": text_for_row(r, records),
             "annotator_screening_status": "", "annotator_primary_event_type": ""}
            for r in selected]
    key = [{"corpus_id": r["corpus_id"], "ref_screening_status": r[SCREEN],
            "ref_primary_event_type": r[PRIMARY]} for r in selected]

    write_csv(OUT_DIR / "iaa_worksheet_BLIND.csv", work,
              ["corpus_id", "acn", "narrative", "annotator_screening_status", "annotator_primary_event_type"])
    write_csv(OUT_DIR / "iaa_answer_key_DO_NOT_SHOW_ANNOTATOR.csv", key,
              ["corpus_id", "ref_screening_status", "ref_primary_event_type"])

    all_rows = rows
    screen_labels = sorted({r[SCREEN] for r in all_rows})
    primary_labels = sorted({r[PRIMARY] for r in all_rows})
    (OUT_DIR / "ALLOWED_LABELS.txt").write_text(
        "screening_status (pick one):\n  " + "\n  ".join(screen_labels) +
        "\n\nprimary_event_type (pick one):\n  " + "\n  ".join(primary_labels) + "\n",
        encoding="utf-8")
    print(f"worksheet: {OUT_DIR / 'iaa_worksheet_BLIND.csv'}  rows={len(work)}")
    print(f"key:       {OUT_DIR / 'iaa_answer_key_DO_NOT_SHOW_ANNOTATOR.csv'}")
    print(f"labels:    {OUT_DIR / 'ALLOWED_LABELS.txt'}")
    print("screening label dist in sample:", dict((c, sum(1 for k in key if k['ref_screening_status']==c)) for c in screen_labels))


def score(worksheet: Path, key_path: Path) -> None:
    work = {r["corpus_id"]: r for r in read_csv(worksheet)}
    key = {r["corpus_id"]: r for r in read_csv(key_path)}
    for task, ann_col, ref_col in [("screening_status", "annotator_screening_status", "ref_screening_status"),
                                   ("primary_event_type", "annotator_primary_event_type", "ref_primary_event_type")]:
        ann, ref = [], []
        for cid, w in work.items():
            a = (w.get(ann_col) or "").strip()
            if a and cid in key:
                ann.append(a); ref.append(key[cid][ref_col])
        if not ann:
            print(f"[{task}] no annotations filled yet"); continue
        agree = sum(a == r for a, r in zip(ann, ref)) / len(ann)
        kappa = cohen_kappa_score(ref, ann)
        print(f"[{task}] n={len(ann)}  percent_agreement={agree:.3f}  cohen_kappa={kappa:.3f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--make", action="store_true")
    p.add_argument("--score", action="store_true")
    p.add_argument("--sample-size", type=int, default=200)
    p.add_argument("--seed", type=int, default=20260619)
    p.add_argument("--worksheet", type=str, default=str(OUT_DIR / "iaa_worksheet_BLIND.csv"))
    p.add_argument("--key", type=str, default=str(OUT_DIR / "iaa_answer_key_DO_NOT_SHOW_ANNOTATOR.csv"))
    a = p.parse_args()
    if a.make:
        make(a.sample_size, a.seed)
    elif a.score:
        score(Path(a.worksheet), Path(a.key))
    else:
        p.error("pass --make or --score")


if __name__ == "__main__":
    main()
