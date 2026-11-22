# Wania: Static analysis, white-box, mutation, and CI

Wania owns Area 1: SonarQube, cyclomatic complexity, unit/white-box testing, mutation testing, and the CI quality gate. BR1–BR4 are project traceability IDs; all four are in Wania's unit-test scope. Fahima covers applicable API cases and Ali covers relevant browser/security cases. The shared rule map is in `docs/team/01-scope-draft.md`.

## Static analysis and complexity

- [ ] Run SonarQube on the agreed source and test scope. Report complexity, duplication, code smells, bugs, vulnerabilities, coverage, technical debt, and ratings in `docs/team/static-analysis.md`.
- [ ] Draw the control-flow graph of one business-rule function, calculate cyclomatic complexity by `E − N + 2P`, and compare it with SonarQube's value. Explain any difference.
- [ ] Save raw Sonar evidence under `docs/team/evidence/area1/`.

## White-box unit testing

- [ ] Define `tests/team/rule_surface.yml` with the in-scope functions and a justified coverage boundary. Coverage and mutation gates measure this agreed rule surface.
- [ ] Write unit tests in `tests/team/unit/` using Indico fixtures and the PostgreSQL test database. Cover BR1–BR4; check with the team that definitions and expected behavior match the frozen v3.3.14 baseline.
- [ ] Reach 100% statement and branch coverage on the agreed rule surface, or justify every uncovered line in `docs/team/unit-testing.md`.
- [ ] Critical MCC/MC/DC target: `Reservation.can_cancel` in `indico/modules/rb/models/reservations.py`. Derive reachable atomic conditions from the implementation; create the complete MCC table, derive MC/DC pairs, and implement the corresponding tests.
- [ ] Write decision tables for every in-scope multi-condition rule and unit-level allowed/disallowed state-transition tests.
- [ ] Record scope, test design, fixtures, commands, results, and evidence in `docs/team/unit-testing.md`.

## Mutation testing and quality gates

- [ ] Implement at least two business-rule-specific custom mutation operators under `tests/team/mutation/`.
- [ ] Run mutation analysis on the rule surface. Analyze at least 15 surviving mutants, classify each as equivalent/missing test/weak assertion, and kill all killable mutants. Write reproducible results in `docs/team/mutation-analysis.md`.
- [ ] Create the unit/coverage and mutation gate scripts, set justified thresholds in `tests/team/quality-gates.yml`, and add the SonarQube, unit/coverage, mutation, API, browser, accessibility/security, and performance jobs to GitHub Actions. Make the required CI gate depend on every required job; no bypasses.
- [ ] Preserve evidence for one documented fix PR (fails before, passes after) and one correctly blocked PR.

## Your two use cases

- [ ] Specify and automate two use cases in Ali's shared Playwright framework. Suggested cases: (1) user submits a booking with a rule violation, corrects it, and succeeds; (2) user checks booking status/timeline after a moderator decision. Include preconditions, main flow, at least two alternatives, at least two exceptions, FR/BR links, and postconditions. Each member owns their own specifications and tests.

## Shared test management

- [ ] Participate with Ali and Fahima in the test plan, three-point estimates, risk register, traceability, weekly reports, defect management/RCA, and completion report. Report your own results, risks, findings, estimated and actual effort.

## Handoffs and completion

- [ ] Publish rule-surface, coverage, mutation, and Sonar commands for the team's CI and evidence plan.
- [ ] Log AI assistance and preserve prompts in `docs/team/ai-use-record.md` / `docs/team/ai-prompts/`. Never report coverage, mutation, or Sonar numbers before actual tool runs.
- [ ] Done when Area 1 analyses and gates are reproducible, unit tests cover BR1–BR4 at the agreed target, and your two use cases run in the shared framework.

## Viva preparation

- [ ] Rerun an owned test and explain every assertion; explain the `can_cancel` MCC/MC/DC table, the coverage boundary, custom operators, surviving-mutant classifications, Sonar metrics, and the CI gate.
