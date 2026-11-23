# MCC and MC/DC for Reservation.can_cancel

## Scope and source

This is the critical-function analysis required for the agreed MCC/MC/DC target. It covers `Reservation.can_cancel` in the pinned Indico v3.3.14 source (`indico/modules/rb/models/reservations.py`, line 451). MCC/MC/DC is scoped to this function; BR1, BR2, and BR4 are not additional MCC targets under the agreed plan.

The function has ten named atomic conditions, but they occur in four sequential decisions. A single flat 1,024-row truth table would be misleading: later decisions are skipped by early returns, Python short-circuiting masks some operands, and rejected/cancelled are mutually exclusive reservation states. Therefore, the tables below enumerate each decision's reachable combinations, identify masked or impossible combinations, and provide a complete MC/DC pair for each atomic condition.

| Label | Atomic condition | Expression / effect |
|---|---|---|
| A | `user is None` | Immediate false return when true |
| B | `is_rejected` | First term of `B or C or D` |
| C | `is_cancelled` | Second term of `B or C or D` |
| D | `is_archived` | Third term of `B or C or D` |
| E | `is_pending` | First operand in `not E and not F` |
| F | An occurrence is within the cancellation grace period | Second operand in `not E and not F` |
| G | User owns the reservation | First term in `G or H or (I and J)` |
| H | User is booked for the reservation | Second term in `G or H or (I and J)` |
| I | `allow_admin` is true | First term in `I and J` |
| J | `rb_is_admin(user)` is true | Second term in `I and J` |

## Reachable combination tables

`—` means the condition is not evaluated or is outside the current decision. It is not a Boolean false. Test names are the row IDs used by `tests/team/unit/can_cancel_mcc_mcdc_test.py`.

### D0 User guard

| Row | A | B–J | Result | Reachable | Test row |
|---|---:|---|---|---|---|
| U0 | 1 | — | False | Yes; immediate return | `test_can_cancel_rejects_missing_user_before_other_conditions` |
| U1 | 0 | — | Continue | Yes | Covered as the precondition for all later decision rows |

### D1 State guard `B or C or D`

The expression returns false if any term is true. Indico reservation state makes B and C mutually exclusive. D can overlap either state, so those combinations remain reachable. Short-circuit order means C is skipped when B=1, and D is skipped when B=1 or C=1.

| Row | B | C | D | Guard | Result | Reachability / evaluation | Test row |
|---|---:|---:|---:|---|---|---|---|
| S0 | 0 | 0 | 0 | False | Continue | Reachable; evaluate all | `mcc-state-000-active` |
| S1 | 1 | — | — | True | False | Reachable rejected state; C,D masked | `mcc-state-100-rejected` |
| S2 | 0 | 1 | — | True | False | Reachable cancelled state; D masked | `mcc-state-010-cancelled` |
| S3 | 0 | 0 | 1 | True | False | Reachable archived state | `mcc-state-001-archived` |
| S4 | 1 | — | 1 | True | False | Reachable rejected + archived; C,D after B are masked | `mcc-state-101-rejected-archived` |
| S5 | 0 | 1 | 1 | True | False | Reachable cancelled + archived; D is evaluated | `mcc-state-011-cancelled-archived` |
| SX | 1 | 1 | 0 or 1 | — | — | Unreachable: rejected and cancelled are mutually exclusive states | Not tested |

### D2 Pending/grace guard `not E and not F`

This guard returns false only for a non-pending reservation with no occurrence within the grace period. A pending reservation bypasses the grace-period query.

| Row | E | F | Guard | Result | Reachability / evaluation | Test row |
|---|---:|---:|---|---|---|---|
| G0 | 1 | — | False | Continue | Reachable; F is masked | `mcc-grace-01-pending-outside-grace` |
| G1 | 0 | 1 | False | Continue | Reachable accepted reservation with eligible occurrence | `mcc-grace-10-accepted-within-grace` |
| G2 | 0 | 0 | True | False | Reachable accepted reservation outside grace | `mcc-grace-11-accepted-outside-grace` |
| GX | 1 | 0 or 1 | — | — | F has no evaluated value when E=1 | `mcc-grace-00-pending-within-grace` and `mcc-grace-01-pending-outside-grace` covers E=1 without asserting F |

### D3 Authorization `G or H or (I and J)`

All combinations within this expression are logically reachable when the earlier guards pass. Short-circuiting masks H when G=1, masks I and J when G or H is true, and masks J when I=0.

| Row | G | H | I | J | Result | Reachability / evaluation | Test row |
|---|---:|---:|---:|---:|---|---|---|
| A0 | 0 | 0 | 0 | — | False | Reachable; J masked | `mcc-final-0000` |
| A1 | 0 | 0 | 1 | 0 | False | Reachable | `mcc-final-0010` |
| A2 | 0 | 0 | 1 | 1 | True | Reachable | `mcc-final-0011` |
| A3 | 0 | 1 | — | — | True | Reachable; I,J masked | `mcc-final-0100` |
| A4 | 1 | — | — | — | True | Reachable; H,I,J masked | `mcc-final-1000` |

The remaining 11 Boolean assignments to G–J are also logically reachable, but evaluate to the same outcome as one of A0–A4 because an earlier true OR operand masks later conditions. Their exact expansions are covered by the parameterized authorization table in the test module. The five rows above are the reduced reachable short-circuit patterns used for MC/DC.

## MC/DC independence pairs

Each pair changes one condition and changes the function result. “Masked” indicates short-circuit evaluation makes that condition irrelevant in the other member of the pair; for the pair listed, the target condition itself is evaluated in both rows.

| Condition | Pair | Inputs held fixed | Result pair | Test rows |
|---|---|---|---|---|
| A: user is None | U0 ↔ S0 | Later inputs are not evaluated for U0; S0 uses an authorized owner | false / true | `test_can_cancel_rejects_missing_user_before_other_conditions` / `mcc-state-000-active` |
| B: rejected | S0 ↔ S1 | C and D masked after B=1 | Continue / false | `mcc-state-000-active` / `mcc-state-100-rejected` |
| C: cancelled | S0 ↔ S2 | B=0; D masked after C=1 | Continue / false | `mcc-state-000-active` / `mcc-state-010-cancelled` |
| D: archived | S0 ↔ S3 | B=0, C=0 | Continue / false | `mcc-state-000-active` / `mcc-state-001-archived` |
| E: pending | G2 ↔ G0 | F is false when evaluated for G2; masked in G0 | false / continue | `mcc-grace-11-accepted-outside-grace` / `mcc-grace-01-pending-outside-grace` |
| F: within grace | G2 ↔ G1 | E=0 | false / continue | `mcc-grace-11-accepted-outside-grace` / `mcc-grace-10-accepted-within-grace` |
| G: owner | A0 ↔ A4 | H,I,J masked when G=1 | false / true | `mcc-final-0000` / `mcc-final-1000` |
| H: booked for | A0 ↔ A3 | G=0; I,J masked when H=1 | false / true | `mcc-final-0000` / `mcc-final-0100` |
| I: allow admin | A5 ↔ A2 | G=0, H=0, J=1 | false / true | `mcc-final-0001` / `mcc-final-0011` |
| J: RB admin | A1 ↔ A2 | G=0, H=0, I=1 | false / true | `mcc-final-0010` / `mcc-final-0011` |

There is one independence pair for each of the ten atomic conditions. The executable suite retains additional cases to document the feasible state-guard and authorization combinations, not just the pair witnesses. For A, the valid-user comparison is a true-returning S0 case with owner=true; the missing-user row returns false before later conditions are evaluated.

## BR3 wording supported by the pinned source

`can_cancel` rejects a missing user, rejected/cancelled/archived reservations, and non-pending reservations without an occurrence in the cancellation grace period. Pending reservations do not require an occurrence in that grace period. After those guards, cancellation is allowed to the owner or booked-for user, or to an RB admin when `allow_admin` is true. Room moderator status alone does not grant cancellation permission.

## Verification status

The test file contains cases for the feasible state rows, both pending/grace outcomes, and the complete 16-combination authorization truth table. The latest verification on 2026-11-23 ran `bash tests/team/run.sh unit`: 102 tests passed, and coverage HTML/XML/JSON reports were generated. The final terminal screenshot is saved at `docs/team/evidence/area1/unit-test-pass-2026-11-23-final.png`; it shows 102 passed in 16.63 seconds. The coverage rollup is in `docs/team/evidence/area1/scoped-coverage-2026-11-23.txt`. MCC/MC/DC completion and statement/branch coverage are separate criteria; both are now complete for their documented targets.
