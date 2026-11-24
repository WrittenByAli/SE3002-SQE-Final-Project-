#!/usr/bin/env python3
"""Fail unless the confirmed BR1–BR4 rule surface meets its coverage gates."""

import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
SCOPE_PATH = ROOT / "tests/team/rule_surface.yml"
GATE_PATH = ROOT / "tests/team/quality-gates.yml"
COVERAGE_PATH = ROOT / "tests/team/reports/unit/coverage.json"


def main():
    scope = yaml.safe_load(SCOPE_PATH.read_text())
    gates = yaml.safe_load(GATE_PATH.read_text())
    coverage = json.loads(COVERAGE_PATH.read_text())
    functions = []
    missing = []
    for item in scope["functions"]:
        key = f"{item['class']}.{item['function']}" if item["class"] else item["function"]
        file_data = coverage["files"].get(item["file"])
        function_data = file_data and file_data.get("functions", {}).get(key)
        if function_data is None:
            missing.append(f"{item['file']}::{key}")
        else:
            functions.append(function_data["summary"])

    if missing:
        raise SystemExit("Coverage data missing scoped functions: " + ", ".join(missing))

    statements = sum(row["num_statements"] for row in functions)
    covered_statements = sum(row["covered_lines"] for row in functions)
    branches = sum(row["num_branches"] for row in functions)
    covered_branches = sum(row["covered_branches"] for row in functions)
    statement_pct = 100.0 * covered_statements / statements if statements else 100.0
    branch_pct = 100.0 * covered_branches / branches if branches else 100.0
    print(f"Rule-surface statements: {covered_statements}/{statements} ({statement_pct:.2f}%)")
    print(f"Rule-surface branches:   {covered_branches}/{branches} ({branch_pct:.2f}%)")

    failures = []
    if statement_pct < gates["coverage"]["statements_percent"]:
        failures.append("statement coverage is below the configured threshold")
    if branch_pct < gates["coverage"]["branches_percent"]:
        failures.append("branch coverage is below the configured threshold")
    if failures:
        raise SystemExit("Coverage gate failed: " + "; ".join(failures))


if __name__ == "__main__":
    main()
