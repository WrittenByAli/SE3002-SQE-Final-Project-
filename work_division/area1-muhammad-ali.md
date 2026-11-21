# Member 1 — Muhammad Ali

## Focus

White-box testing of the room-booking business rules, coverage, and mutation analysis.

## Own these deliverables

- `tests/team/rule_surface.yml`: define the in-scope business-rule functions and explain the boundary of the coverage scope.
- `tests/team/unit/`: write unit tests for BR1–BR4 using Indico's fixtures and the test database.
- MCC and MC/DC: produce the complete condition-combination table and MC/DC pairs for `Reservation.can_cancel`, then implement the required tests. Keep the target decision consistent with `CLAUDE.md` and the finalized scope document.
- Decision tables for the other rules with multiple conditions, plus allowed and disallowed state transitions.
- Coverage gate scripts for the rule surface; report statement and branch coverage and work toward 100% for both.
- Mutation testing on the rule surface; add at least two business-rule-specific mutation operators and analyze at least 15 surviving mutants. Classify each as equivalent, missing test, or weak assertion, and kill the killable mutants.
- `docs/team/unit-testing.md`, `docs/team/mutation-analysis.md`, and evidence for your results.
- Two use cases: moderator approves a pending booking and moderator rejects a pending booking. Write the specifications and tests using Member 3's shared Playwright framework.

## Shared lead responsibility

- Draft the test plan and estimates with input from the other two members.
- Finalize `docs/team/01-scope-draft.md`; confirm that the FR/BR IDs and rule definitions match the running system and the tests.

## Handoffs

- Publish the agreed rule surface and stable rule IDs before Members 2 and 3 finalize their test cases.
- Give Member 2 the coverage and mutation commands that CI must run; Member 2 owns wiring them into CI.
- Use Member 3's agreed Playwright directory and fixtures for the two UI use cases. Do not create a separate E2E framework or competing test directory.

## Done when

- The rule-surface gate reports the achieved statement and branch coverage, with a documented plan for any remaining gap.
- MCC/MC/DC tables and tests are reviewed against the chosen decision.
- Mutation results and surviving-mutant analysis are reproducible from the documented command.
- The two moderator use cases are specified and automated.

