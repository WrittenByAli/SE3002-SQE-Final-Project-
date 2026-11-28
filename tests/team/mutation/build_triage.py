#!/usr/bin/env python3
"""Build the reviewed initial-survivor CSV from two Cosmic Ray databases."""

import csv
import sqlite3
import sys
from pathlib import Path


HEADERS = [
    "mutant_id", "rule", "module_path", "operator", "occurrence", "function",
    "line", "column", "end_line", "end_column", "initial_result", "classification", "rationale",
    "final_result", "fix_or_evidence",
]


def rule_and_test(module, function, diff):
    if function == "_validate_room_booking_limit":
        return "BR1", "tests/team/unit/br1_br4_booking_rules_test.py::test_br1_booking_length_boundary"
    if function == "is_booking_start_within_grace_period":
        return "BR1", "tests/team/unit/br1_br4_booking_rules_test.py::test_br1_grace_period_with_no_limit_uses_server_local_date"
    if function == "can_accept":
        return "BR2", "tests/team/unit/br2_br3_authorization_test.py::test_br2_can_accept_decision_table"
    if function == "can_reject":
        return "BR3", "tests/team/unit/br2_br3_authorization_test.py::test_br3_can_reject_decision_table"
    if function == "can_cancel":
        return "BR3", "tests/team/unit/br2_br3_authorization_test.py::test_br3_can_cancel_decision_table"
    if function in {"cancel", "reject"}:
        name = "test_br3_cancel_state_change" if function == "cancel" else "test_br3_reject_state_change"
        return "BR3", f"tests/team/unit/br2_br3_authorization_test.py::{name}"
    if function in {"can_book", "can_prebook"}:
        return "BR4", "tests/team/unit/br1_br4_booking_rules_test.py::test_br4_room_or_location_permission_accepts_room_acl"
    if function == "_process" and any(
            line.startswith("-") and "ignore_admin=(not admin_override)" in line and not line.startswith("---")
            for line in diff.splitlines()):
        return "BR1", "tests/team/unit/booking_workflow_coverage_test.py::test_br1_create_handler_passes_admin_override"
    if function == "_process" and any(
            line.startswith("-") and "args.get('link_type')" in line and not line.startswith("---")
            for line in diff.splitlines()):
        return "BR4", "tests/team/unit/booking_workflow_coverage_test.py::test_br1_create_handler_ignores_incomplete_optional_link"
    if function == "_process":
        return "BR3", "tests/team/unit/booking_workflow_coverage_test.py::test_br3_state_action_dispatch"
    if function == "create_from_data":
        return "BR4", "tests/team/unit/booking_workflow_coverage_test.py::test_br4_create_from_data_ignores_admin_override_when_requested"
    raise ValueError(f"No rule/test mapping for {module}:{function}")


def changed_lines(diff):
    removed, added = [], []
    for line in diff.splitlines():
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-"):
            removed.append(line[1:].strip())
        elif line.startswith("+"):
            added.append(line[1:].strip())
    return " ; ".join(removed), " ; ".join(added)


def load_initial(initial_db):
    connection = sqlite3.connect(initial_db)
    connection.row_factory = sqlite3.Row
    return connection.execute(
        """SELECT m.*, r.diff FROM mutation_specs AS m
           JOIN work_results AS r USING (job_id)
           WHERE r.test_outcome = 'SURVIVED'
           ORDER BY m.module_path, m.definition_name, m.start_pos_row,
                    m.operator_name, m.occurrence"""
    ).fetchall()


def result_index(final_db):
    connection = sqlite3.connect(final_db)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """SELECT m.module_path, m.operator_name, m.occurrence,
                  m.definition_name, m.start_pos_row, m.start_pos_col,
                  m.end_pos_row, m.end_pos_col, r.test_outcome
           FROM mutation_specs AS m JOIN work_results AS r USING (job_id)"""
    ).fetchall()
    return {
        (r["module_path"], r["operator_name"], r["occurrence"], r["definition_name"],
         r["start_pos_row"], r["start_pos_col"], r["end_pos_row"], r["end_pos_col"]): r["test_outcome"]
        for r in rows
    }


def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: build_triage.py INITIAL.sqlite FINAL.sqlite OUTPUT.csv")
    initial_db, final_db, output = map(Path, sys.argv[1:])
    final = result_index(final_db)
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS, lineterminator="\n")
        writer.writeheader()
        for mutant in load_initial(initial_db):
            key = (mutant["module_path"], mutant["operator_name"], mutant["occurrence"],
                   mutant["definition_name"], mutant["start_pos_row"], mutant["start_pos_col"],
                   mutant["end_pos_row"], mutant["end_pos_col"])
            result = final.get(key)
            if result not in {"KILLED", "SURVIVED"}:
                raise SystemExit(f"Missing final outcome for initial survivor {mutant['job_id']}: {key}")
            rule, evidence = rule_and_test(mutant["module_path"], mutant["definition_name"], mutant["diff"])
            removed, added = changed_lines(mutant["diff"])
            line, column = mutant["start_pos_row"], mutant["start_pos_col"]

            if result == "SURVIVED":
                classification = "equivalent"
                final_result = "equivalent-survivor"
                if mutant["definition_name"] == "_validate_room_booking_limit":
                    rationale = ("The calculation compares timedelta.days, which floors to whole days. "
                                 "Changing the final clock minute from 23:59 to 23:58 or 22:59 leaves "
                                 "the day-delta unchanged for every end date.")
                elif mutant["operator_name"].endswith("Eq_LtE"):
                    rationale = ("RepeatFrequency.NEVER is the minimum supported enum value (0); all "
                                 "other schema values are greater, so == NEVER and <= NEVER select "
                                 "the same supported inputs.")
                elif mutant["operator_name"].endswith("Eq_Is"):
                    rationale = ("RepeatFrequency is an Enum and its members are singletons; the "
                                 "schema supplies the enum member, so equality and identity agree "
                                 "for supported inputs.")
                else:
                    raise SystemExit(f"Unreviewed final survivor: {mutant['job_id']} {mutant['operator_name']}")
                fix_or_evidence = f"{evidence}; source-domain proof at {mutant['module_path']}:{line}"
            else:
                final_result = "killed"
                classification = "weak-assertion" if mutant["definition_name"] in {"cancel", "reject"} else "missing-test"
                rationale = (f"Initial run left this change alive: {removed!r} -> {added!r}. "
                             "The relevant decision/state path did not distinguish the original behavior "
                             "from this mutation; the focused regression below now checks that outcome.")
                fix_or_evidence = evidence

            writer.writerow({
                "mutant_id": mutant["job_id"], "rule": rule, "module_path": mutant["module_path"],
                "operator": mutant["operator_name"], "occurrence": mutant["occurrence"],
                "function": mutant["definition_name"], "line": line, "column": column,
                "end_line": mutant["end_pos_row"], "end_column": mutant["end_pos_col"],
                "initial_result": "survived", "classification": classification,
                "rationale": rationale, "final_result": final_result,
                "fix_or_evidence": fix_or_evidence,
            })
    print(f"Wrote {len(load_initial(initial_db))} initial survivor dispositions to {output}")


if __name__ == "__main__":
    main()
