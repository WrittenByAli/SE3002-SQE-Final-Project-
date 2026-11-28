#!/usr/bin/env python3
"""Enforce Cosmic Ray completeness, score, and evidence-backed survivor triage."""

import csv
import re
import sqlite3
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
GATE_PATH = ROOT / "tests/team/quality-gates.yml"
REPORT_PATH = ROOT / "tests/team/reports/mutation/cr-report-final.txt"
DB_PATH = ROOT / "tests/team/reports/mutation/area1-final.sqlite"
TRIAGE_PATH = ROOT / "tests/team/mutation/survivor-triage.csv"


def _count(pattern, text, label):
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        raise SystemExit(f"Cannot find {label} in {REPORT_PATH}")
    return int(match.group(1))


def _key(row):
    return (
        row["module_path"], row["operator"], int(row["occurrence"]), row["function"],
        int(row["line"]), int(row["column"]), int(row["end_line"]), int(row["end_column"]),
    )


def _load_final_results():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """SELECT m.module_path, m.operator_name, m.occurrence, m.definition_name,
                      m.start_pos_row, m.start_pos_col, m.end_pos_row, m.end_pos_col,
                      r.worker_outcome, r.test_outcome
               FROM mutation_specs AS m JOIN work_results AS r USING (job_id)"""
        ).fetchall()
    results = {}
    for row in rows:
        key = (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
        if row[8] != "NORMAL" or row[9] not in {"KILLED", "SURVIVED"}:
            raise SystemExit(f"Incompetent or incomplete mutant result for {key}: {row[8:]}")
        results[key] = row[9]
    return results


def main():
    gates = yaml.safe_load(GATE_PATH.read_text())["mutation"]
    report = REPORT_PATH.read_text()
    total = _count(r"total jobs:\s*(\d+)", report, "total mutation count")
    complete = _count(r"complete:\s*(\d+)", report, "completed mutation count")
    surviving = _count(r"surviving mutants:\s*(\d+)", report, "surviving mutation count")
    outcomes = re.findall(
        r"worker outcome: WorkerOutcome\.(\w+), test outcome: TestOutcome\.(\w+)", report
    )

    if total == 0 or complete != total:
        raise SystemExit(f"Mutation campaign incomplete: {complete}/{total} jobs completed")
    allowed_outcomes = {("NORMAL", "KILLED"), ("NORMAL", "SURVIVED")}
    if len(outcomes) != total or any(result not in allowed_outcomes for result in outcomes):
        raise SystemExit("Mutation report has missing or non-normal/incompetent mutant results")
    score = 100.0 * (total - surviving) / total
    print(f"Cosmic Ray mutation score: {score:.2f}% ({total - surviving}/{total})")
    if score < gates["minimum_score_percent"]:
        raise SystemExit(f"Mutation score is below {gates['minimum_score_percent']}%")

    with TRIAGE_PATH.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) < gates["minimum_survivors_reviewed"]:
        raise SystemExit(
            f"Review at least {gates['minimum_survivors_reviewed']} initial survivors; found {len(rows)}"
        )

    final_results = _load_final_results()
    approved_equivalents = set()
    seen = set()
    valid_classes = {"equivalent", "missing-test", "weak-assertion"}
    for row in rows:
        key = _key(row)
        if key in seen:
            raise SystemExit(f"Duplicate survivor triage key: {key}")
        seen.add(key)
        actual = final_results.get(key)
        if actual is None:
            raise SystemExit(f"Initial survivor is missing from final campaign: {row['mutant_id']} {key}")
        if row["initial_result"] != "survived" or row["classification"] not in valid_classes:
            raise SystemExit(f"Incomplete survivor classification: {row['mutant_id']}")
        if not row["rationale"].strip() or not row["fix_or_evidence"].strip():
            raise SystemExit(f"Missing rationale or evidence for {row['mutant_id']}")

        if actual == "SURVIVED":
            if row["classification"] != "equivalent" or row["final_result"] != "equivalent-survivor":
                raise SystemExit(f"Unresolved surviving mutant: {row['mutant_id']} {key}")
            approved_equivalents.add(key)
        else:
            if row["classification"] == "equivalent" or row["final_result"] != "killed":
                raise SystemExit(f"Incorrect final mutant disposition: {row['mutant_id']} {key}")

    final_survivors = {key for key, result in final_results.items() if result == "SURVIVED"}
    if final_survivors != approved_equivalents:
        unresolved = final_survivors - approved_equivalents
        stale = approved_equivalents - final_survivors
        raise SystemExit(f"Survivor triage does not match campaign; unresolved={unresolved}, stale={stale}")
    print(f"Reviewed {len(rows)} initial survivors; {len(approved_equivalents)} equivalent survivors verified from the final database")


if __name__ == "__main__":
    main()
