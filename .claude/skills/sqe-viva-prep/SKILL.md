---
name: sqe-viva-prep
description: "Prepare a member for the SQE viva. Rerun a selected test and explain each assertion, rehearse the live task (business-rule change or updated API spec: predict failing tests and gates, make the change, show the result), and quiz on every component they own. Use for \"viva\", \"practice\", \"live task\", \"quiz me\", \"mock exam\"."
---

# Viva preparation (20 marks, individual)

The viva checks **every** component. If you can't explain it, it can be marked to zero, and "we did it but forgot" is not accepted.

## Drill 1: rerun + explain (5 min)
Pick a test from the member's area at random (`grep -rn "def test_\|test(" tests/team/<area>`). The member runs it alone and
explains: technique, rule ID, input choice (why that value), each assertion, what a failure would mean.

## Drill 2: live task (15 min, timed)
Draw one at random and let the **member** predict before changing anything:
1. BR1: `booking_limit_days` becomes exclusive (`<`). → BR1 BVA unit test "at limit" fails, API BVA at 7 days flips, mutation gate
   unaffected or improved; CI `unit` + `app-tests` red.
2. BR2: moderators may approve accepted bookings again. → decision-table row 3 fails; state-transition API test fails.
3. Spec: `x-booking-limit-days: 5`. → regenerate; cases at 5/6 now expect reject; API tests vs unchanged app fail → mismatch report.
4. Spec: `reason` becomes required with `minLength: 3`. → new EP invalid classes + BVA 2/3/4.
5. BR3: an accepted booking's cancellation grace-period guard changes. → update the BR3 transition/decision cases and the `can_cancel` MCC rows; predict the unit, API, and mutation gates affected.
Then make the change on a branch, run `bash tests/team/run.sh unit|api`, open a PR, and show which CI gate went red and why.

## Drill 3: component quiz
Use the `viva-examiner` agent on the member's area + one shared component (risk register, traceability, GQM, AI-use record).
Score honestly; list what to study, and repeat until all components are green.
