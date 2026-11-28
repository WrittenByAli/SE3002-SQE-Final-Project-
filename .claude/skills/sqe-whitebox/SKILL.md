---
name: sqe-whitebox
description: "Wania's white-box unit testing for the Indico rule surface. 100% statement+branch coverage, decision tables, state transitions, complete MCC table and MC/DC pairs for the critical function (Reservation.can_cancel). Use for unit tests, coverage gaps, MCC, MC/DC, and \"why is this branch uncovered\"."
---

# White-box unit testing (Wania owns; 16 marks)

Scope = the business-rule functions you list in `tests/team/rule_surface.yml` (candidates in `CLAUDE.md`). Run:
`bash tests/team/run.sh unit` → `tests/team/reports/unit/coverage.{json,xml}` + `htmlcov/`. Coverage.py reports per **file**,
so build a small gate that narrows `coverage.json` to your rule functions (use `ast` to get each function's line span).

## Writing tests (Indico fixtures, real PostgreSQL)
- Files `tests/team/unit/<rule>_<topic>_test.py`; Indico's plugin gives fixtures: `db`, `create_user(id, rb_admin=..)`,
  `create_room(**cols)`, `dummy_room`, `create_reservation(state=..., start_dt=..., booked_for_user=..)`, `dummy_user`.
- Room moderator: `room.update_principal(user, permissions={'moderate'})`. RB admin: `create_user(id, rb_admin=True)`.
- Pure helpers can be called unbound: `RHCreateBooking._validate_room_booking_limit(None, start, end, limit)`.
- Controller guards (`RHBookingStateActions._check_access`): build the RH with `rh = RHBookingStateActions(); rh.booking = b;
  rh.action = 'approve'` and patch `session.user` with Indico's `request_context`/`app` fixtures, or monkeypatch
  `RHBookingBase._check_access` to a no-op so only the rule logic is under test. Assert `ExpectedError`/`Forbidden`.
- **Import gotcha (verified):** importing an Indico controller/model at module level in a test that uses no DB fixture fails with
  `InvalidRequestError ... failed to locate a name ("APIKey")`, because the SQLAlchemy mappers aren't configured yet. Fix: call
  `from indico.core.db.sqlalchemy.util.models import import_all_models; import_all_models()` before the import (the app does the same).
- `pytest.ini` turns warnings into errors. Fix the cause, never filter it away to make a test pass.
- Name/docstring every test with rule + technique + row id (e.g. `test_br3_can_cancel_mcc_row_07`).

## MCC → MC/DC for `Reservation.can_cancel` (critical module)
Atomic conditions (v3.3.14):
`A user is None` · `B is_rejected` · `C is_cancelled` · `D is_archived` · `E is_pending` · `F occurrence within cancel grace`
· `G is_owned_by(user)` · `H is_booked_for(user)` · `I allow_admin` · `J rb_is_admin(user)`.
1. Write the full **MCC table** of the combinations the short-circuit code can actually reach (list unreachable ones and why;
   that is the MCC/short-circuit argument examiners look for). Columns: row, A..J, outcome.
2. For each condition, pick **MC/DC pairs**: two rows from the MCC table that differ only in that condition (others fixed or
   masked by short-circuit) and give different outcomes. Table: condition | row x | row y | outcome x/y.
3. Minimal test set = union of the pair rows (≈ N+1). Implement exactly those rows and cite the row ids.
Template: `docs/team/templates/mcc-mcdc.md`. Deliverable: `docs/team/unit-testing.md`.

## CFG + cyclomatic complexity
Wania owns the CFG and hand calculation. Draw the graph of the selected business-rule function (nodes = basic blocks; split compound boolean conditions as decisions for comparison with Sonar), compute V(G) = E − N + 2P, and compare with Sonar's function complexity. Cognitive complexity is a separate metric.

## Done when
Coverage gate at 100/100 for the rule surface, every uncovered line justified, all 4 rules + all decision tables + all state
transitions covered, MCC + MC/DC tables match the tests, thresholds in `tests/team/quality-gates.yml` raised in the same PR.
