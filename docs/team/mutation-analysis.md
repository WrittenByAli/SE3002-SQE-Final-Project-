# Area 1 mutation analysis

## Scope and tool

Tool: Cosmic Ray, pinned in `tests/team/requirements.txt`. The mutated modules are the four Python files containing the confirmed server-side BR1–BR4 functions listed in `tests/team/rule_surface.yml`: booking controller, reservation model, room model, and booking utility. Cosmic Ray runs the team unit suite from the Linux/Python 3.12 test runner.

Run from the repository root with the test database available:

```bash
bash tests/team/run.sh mutation run
```

The command runs the operator self-tests, initializes a new campaign, verifies the unmutated baseline, executes the mutations, and writes the Cosmic Ray text/HTML reports under `tests/team/reports/mutation/`.

## Custom business-rule operators

The operators are implemented as Cosmic Ray plug-ins in `tests/team/mutation/sqe_indico_mutation/operators.py` and registered in `tests/team/mutation/pyproject.toml`.

| Operator | Rule | Mutation | Why it matters |
|---|---|---|---|
| `BR1BookingLimitBoundary` | BR1 | Changes `selected_period_days <= booking_limit_days` to `<` in `_validate_room_booking_limit`. | Detects a test suite that misses a booking exactly at the configured limit. |
| `BR3CancellationGraceGuard` | BR3 | Changes the pending/grace-period conjunction in `Reservation.can_cancel` from `and` to `or`. | Detects missing tests for pending reservations and accepted reservations inside/outside the grace period. |

`tests/team/mutation/test_operators.py` checks that each operator changes only its intended business-rule function. The project uses Cosmic Ray because it supports user-defined mutation operators through its operator-provider plug-in API. [Cosmic Ray operator documentation](https://cosmic-ray.readthedocs.io/en/latest/how-tos/operators.html)

## Thresholds

The CI mutation threshold is 90% killed out of all generated mutants. The four business rules include booking authorization and state-changing actions, so this threshold rejects the initial 82.04% result while allowing well-justified equivalent survivors after tests are strengthened. The campaign must complete without incompetent mutants. At least 15 initial survivors must be individually classified as equivalent, missing-test, or weak-assertion. Every non-equivalent survivor must be killed by an added/strengthened test; an equivalent survivor must have a code-specific rationale. All 44 initial survivors are analyzed in `tests/team/mutation/survivor-triage.csv`. `tests/team/mutation/build_triage.py` reproduces the dispositions by matching the initial and final SQLite sessions on module, operator, function, and source position.

The CI quality gate reads the actual final Cosmic Ray SQLite session, verifies that the campaign is complete and all worker outcomes are valid, recomputes the score from the text report, and confirms that each recorded survivor disposition matches its final database outcome. It also rejects any final survivor that is not individually approved as equivalent.

The SonarQube server quality gate must enforce the new-code limits recorded in
`tests/team/quality-gates.yml`: coverage at least 80%, zero new bugs and
vulnerabilities, A ratings for reliability, security and maintainability, no
more than 3% duplicated new lines, and 100% review of new security hotspots.
The independent BR1–BR4 unit gate remains stricter at 100% statements and
branches on the confirmed rule surface. CI waits for the SonarQube quality-gate
result, so a missing or failed server-side gate blocks `CI gate`.

## Results

| Run | Date | Generated | Killed | Survived | Equivalent survivors | Mutation score | Evidence |
|---|---|---:|---:|---:|---:|---:|---|
| Initial campaign, before survivor fixes | 2026-11-24 | 245 | 201 | 44 | Not yet classified | 82.04% | `docs/team/evidence/area1/mutation-report-initial.txt` |
| Final campaign, after focused tests | 2026-11-24 | 245 | 241 | 4 | 4 | 98.37% | `docs/team/evidence/area1/mutation-report-final.txt`; `tests/team/mutation/survivor-triage.csv` |

The final four survivors are equivalent for the defined input domain: changing 23:59 to 23:58 or 22:59 does not change the whole-day `timedelta.days` result; `RepeatFrequency.NEVER` is the minimum supported enum member, making `== NEVER` and `<= NEVER` equivalent; and `RepeatFrequency` members are enum singletons, making equality and identity equivalent for schema-validated inputs. All 40 other initial survivors were killed by focused regressions. The raw score does not count these four as kills.

The initial score would fail the 90% gate (82.04% < 90%). After tests were added for authorization combinations, admin override propagation, date boundaries, repeated reservations, optional links, and cancellation/rejection side effects, the final score passes (98.37% >= 90%). This provides a repeatable pre-fix failure and post-fix pass for the PR demonstration; the GitHub PR status screenshots are still to be captured after remote setup.
