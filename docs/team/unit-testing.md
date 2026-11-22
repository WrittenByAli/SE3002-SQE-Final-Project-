# White-box unit testing

## Rule surface and scope

The candidate coverage surface is listed in [`tests/team/rule_surface.yml`](../../tests/team/rule_surface.yml). It covers the server-side functions implementing BR1–BR4 for the selected room-booking workflows. The list is **proposed for team review**, not frozen yet. Wania should review the functions with Fahima and Ali before using it as the final denominator for the coverage gate.

The upstream source is frozen at Indico `v3.3.14`, commit `a42252ead3509f9b31db0691cc9af899ab18416e`. The team test suite is in `tests/team/unit/`; do not edit upstream code just to make coverage pass.

## Day 1 baseline

| Item | Starting result | Evidence / status |
|---|---|---|
| Team unit tests | At the start of Day 1, no team-authored unit-test files existed. Initial BR1–BR4 decision tests have now been added and pass in the Docker runner. | `tests/team/unit/`; initial files: `br1_br4_booking_rules_test.py`, `br2_br3_authorization_test.py` |
| First team test run | 25 passed, 0 failed. This is an initial decision-test set, not completion of the full scope. | `bash tests/team/run.sh unit`; `tests/team/reports/unit/junit.xml` |
| Initial module-wide coverage | 24% statements, 3% branches across all of `indico/modules/rb`; this broad denominator includes functions outside the proposed rule surface. | `tests/team/reports/unit/coverage.json` and `coverage.xml` |
| Rule-surface coverage | Not yet calculated separately. A function-level coverage gate is still needed before comparing against the 100% scoped target. | Do not use the module-wide figures as the scoped result. |
| Scope file | Proposed candidate list created | `tests/team/rule_surface.yml`, pending teammate review |
| SonarQube | Not yet run | Docker-based SonarQube is being set up; record actual scan/date/commit after it completes |

The starting state had no team-authored tests; the initial test set now runs. Keep the first run's module-wide coverage separate from the final scoped target. Do not enter Sonar metrics until they come from a real scan.

## Coverage results

| Function | Statements | Branches | Missing paths | Justification if uncovered |
|---|---:|---:|---|---|
| _Pending function-level analysis; initial module-wide run completed_ | | | | |

Coverage command: `bash tests/team/run.sh unit`. Reports: `tests/team/reports/unit/coverage.json`, `coverage.xml`, and `htmlcov/`.
The captured command output is `docs/team/evidence/area1/unit-test-run.txt`. For the PDF, capture a terminal screenshot with the command, `25 passed`, and report-generation lines visible; save it as `docs/team/evidence/area1/unit-test-pass.png`.

## Business rules and techniques

| Rule | Test cases | Techniques | Result |
|---|---|---|---|
| BR1 — booking start and length limit | Booking-length and grace-period boundary cases authored. | Equivalence classes, boundaries, rule-function tests | Included in 25 passing tests; more branches remain |
| BR2 — approval eligibility | Pending/accepted reservation × moderator/non-moderator cases authored. | Decision table | Included in 25 passing tests |
| BR3 — guarded state transitions and cancellation | Rejection eligibility and cancellation authorization cases authored; lifecycle action tests and complete MCC/MC/DC pairs remain. | State transitions, decision tables, MCC/MC/DC for `Reservation.can_cancel` | Included in 25 passing tests; incomplete |
| BR4 — direct-book and pre-book permissions | Public-room booking mode and anonymous-user cases authored. | Decision table | Included in 25 passing tests; more permission branches remain |

## Decision tables and state transitions

_Add the completed decision tables and allowed/disallowed state-transition cases after reviewing the rule surface with the team._

## Critical function MCC and MC/DC

Critical function: `Reservation.can_cancel` in `indico/modules/rb/models/reservations.py`. First derive the reachable atomic conditions from the implementation and document the MCC combinations; then select MC/DC independence pairs from that table and link each pair to implemented test names. The tables and tests are pending.
