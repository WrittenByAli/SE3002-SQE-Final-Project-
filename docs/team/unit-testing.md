# White-box unit testing

## Rule surface and scope

The confirmed coverage surface is listed in [`tests/team/rule_surface.yml`](../../tests/team/rule_surface.yml). It covers the selected server-side functions implementing BR1–BR4 in the room-booking workflows. The team confirmed this scope before the final coverage run. It does not claim to cover every function in Indico.

The upstream source is frozen at Indico `v3.3.14`, commit `a42252ead3509f9b31db0691cc9af899ab18416e`. The team test suite is in `tests/team/unit/`; do not edit upstream code just to make coverage pass.

## Day 1 baseline

| Item | Starting result | Evidence / status |
|---|---|---|
| Team unit tests | At the start of Day 1, no team-authored unit-test files existed. Initial BR1–BR4 decision tests have now been added and pass in the Docker runner. | `tests/team/unit/`; initial files: `br1_br4_booking_rules_test.py`, `br2_br3_authorization_test.py` |
| First team test run | 25 passed, 0 failed. This is the initial decision-test set, not completion of the full scope. | `docs/team/evidence/area1/unit-test-run.txt` |
| MCC/MC-DC follow-up run | 52 passed, 0 failed after adding 27 focused `can_cancel` cases. | `docs/team/evidence/area1/unit-test-run-2026-11-22.txt`; generated reports under `tests/team/reports/unit/` |
| Module-wide coverage after the 52-test run | 24% statements, 3% branches across all of `indico/modules/rb`; this broad denominator includes functions outside the proposed rule surface. | `tests/team/reports/unit/coverage.json` and `coverage.xml` |
| Confirmed rule-surface coverage | Final run: 155/155 statements and 78/78 branches (100% each) across the confirmed BR1–BR4 function list. | `docs/team/evidence/area1/scoped-coverage-2026-11-23.txt`; full generated coverage reports under `tests/team/reports/unit/` |
| Scope file | Team-confirmed list | `tests/team/rule_surface.yml`, status `confirmed_by_team` |
| SonarQube | A local scan completed; overview showed 12.5% project coverage and a passed Quality Gate. | `docs/team/static-analysis.md`; project-wide mixed-language coverage is not the scoped Python coverage |

The starting state had no team-authored tests; the initial test set ran successfully. The latest report supersedes the historical 52-test results below. Keep module-wide coverage separate from the selected BR1–BR4 scope.

## Coverage results

| Function | Statements | Branches | Missing paths | Justification if uncovered |
|---|---:|---:|---|---|
| Confirmed BR1–BR4 function list | 155/155 (100%) | 78/78 (100%) | None in the selected function list. | Final scoped rollup from the 102-test run; see the per-rule evidence file |

Coverage command: `bash tests/team/run.sh unit`. Current reports: `tests/team/reports/unit/coverage.json`, `coverage.xml`, and `htmlcov/`.
Captured outputs: `docs/team/evidence/area1/unit-test-run.txt` (initial 25-test run), `docs/team/evidence/area1/unit-test-run-2026-11-22.txt` (historical 52-test run), and `docs/team/evidence/area1/unit-test-pass-2026-11-23-final.png` (102 passed in 16.63 seconds; coverage HTML/XML/JSON generated). The per-rule coverage rollup is recorded in `docs/team/evidence/area1/scoped-coverage-2026-11-23.txt`.

## Business rules and techniques

| Rule | Test cases | Techniques | Result |
|---|---|---|---|
| BR1 — booking start and length limit | Grace-period and booking-length boundaries; create-request guard and link handling branches. | Equivalence classes, boundaries, rule-function tests | 100% statements and branches in the selected BR1 functions |
| BR2 — approval eligibility | Pending/accepted and moderator eligibility cases. | Decision table | 100% statements and branches in the selected BR2 functions |
| BR3 — guarded state transitions and cancellation | MCC/MC/DC for `Reservation.can_cancel`; accept/reject/cancel state operations; moderator access, collision and dispatch cases. | State transitions, decision tables, MCC/MC/DC for `Reservation.can_cancel` | 100% statements and branches in the selected BR3 functions |
| BR4 — direct-book and pre-book permissions | Direct/pre-book permission rules, request authorization and reservation creation modes. | Decision table, boundary tests | 100% statements and branches in the selected BR4 functions |

## Decision tables and state transitions

The decision tables and state-transition cases are recorded in the coverage tests and [`mcc-mcdc.md`](mcc-mcdc.md). The current scoped run reports no uncovered statements or branches.

## Critical function MCC and MC/DC

Critical function: `Reservation.can_cancel` in `indico/modules/rb/models/reservations.py`. The source-aligned reachable-combination tables, masked/unreachable cases, and one MC/DC pair for each of the ten atomic conditions are in [`mcc-mcdc.md`](mcc-mcdc.md); executable cases are in `tests/team/unit/can_cancel_mcc_mcdc_test.py`. The latest complete unit run passed 102 tests and the confirmed BR1–BR4 function list reached 155/155 statements and 78/78 branches. This is scoped coverage, not 100% coverage of all Indico code.
