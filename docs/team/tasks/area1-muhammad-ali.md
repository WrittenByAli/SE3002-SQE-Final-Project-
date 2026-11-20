# Area 1: Muhammad Ali: Static analysis, white-box, mutation, CI (29 marks + leads)

Skills: `sqe-sonar`, `sqe-whitebox`, `sqe-mutation`, `sqe-ci-gate`. Agents: `mutant-analyst`, `rubric-auditor`, `viva-examiner`.
Commands: `bash tests/team/run.sh unit | mutation` (Linux runner: Python 3.12 + PostgreSQL + mutmut 3.8.1, ready to use).
You create: `tests/team/rule_surface.yml` (the business-rule functions in scope; the candidate list is in `CLAUDE.md`),
`tests/team/quality-gates.yml` (thresholds), the coverage/mutation gate scripts in `tests/team/tools/`, and the CI test jobs.

## 1. Static analysis & metrics (5 marks)

- [ ] Run SonarQube Community on the repo. CI does it automatically (`sonarqube` job); also run it locally once (`sqe-sonar` skill).
- [ ] Report **complexity, duplication, code smells, bugs, vulnerabilities, coverage, technical debt, ratings** for
      `indico/modules/rb` and `tests/team`, and explain what each metric shows about quality and risk.
      → `docs/team/static-analysis.md` (template: `docs/team/templates/static-analysis.md`)
- [ ] Hand-draw the **CFG** of one business-rule function (recommended: `Reservation.can_cancel`), compute
      **V(G) = E − N + 2 = P + 1 = regions**, and compare it with SonarQube's cyclomatic complexity for that function. Explain any
      difference (Sonar counts boolean operators `and`/`or` as decisions).
- [ ] Evidence: Sonar screenshot/JSON export in `docs/team/evidence/area1/`.

## 2. White-box unit testing (16 marks, the biggest component)

- [ ] Define the rule surface (`tests/team/rule_surface.yml`) and a gate that measures **statement + branch coverage of
      exactly those functions** (coverage.py reports per file; the functions sit inside big files). Justify the scope in the test plan.
- [ ] **100% statement and branch coverage** of the rule surface. Justify any uncovered line in `docs/team/unit-testing.md`.
- [ ] Cover all **four business rules** (BR1–BR4) in `tests/team/unit/*_test.py` (Indico fixtures + real PostgreSQL, see `sqe-whitebox`).
- [ ] **Critical module = `Reservation.can_cancel`**: write the complete **MCC table** (every combination of the atomic
      conditions that can be reached), then derive the **MC/DC pairs** from it (for each condition, two rows that differ only in
      that condition and flip the outcome). Implement one test per needed row. → `docs/team/unit-testing.md`
- [ ] Decision tables for every rule with ≥2 conditions (`can_accept`, `can_reject`, `can_book`, `can_prebook`, `_check_access`).
- [ ] State transitions: every allowed transition + ≥1 disallowed from each state (pending, accepted, rejected, cancelled).
- [ ] Thresholds in `tests/team/quality-gates.yml`; raise them as you earn them (ratchet; the guard hook blocks lowering). Final = 100.

## 3. Mutation analysis & CI quality gate (8 marks)

- [ ] Run mutmut on the rule surface (`bash tests/team/run.sh mutation`) and report the score.
- [ ] Add **≥2 custom mutation operators** based on the business rules (e.g. `<=`→`<` on the booking limit,
      swap `is_pending`↔`is_accepted`, drop `allow_admin and`). Put them in `tests/team/mutation/`; see `sqe-mutation`.
- [ ] Analyse **≥15 surviving mutants**: classify each as equivalent / missing test / weak assertion, then kill the
      killable ones. → `docs/team/mutation-analysis.md` (use the `mutant-analyst` agent; check every verdict yourself)
- [ ] CI (`.github/workflows/ci.yml`) already runs the **prerequisite** jobs (harness check, runner build, app boot + seed).
      Add the **gate jobs**: SonarQube, unit + coverage gate, mutation gate, API, E2E, wired into the `CI gate` job that branch
      protection requires. **No escape hatches** (`check_harness.py` enforces it).
- [ ] Justify each threshold from evidence → `docs/team/ci-quality-gate.md`.
- [ ] **Documented fix PR**: a defect (GitHub Issue) whose test fails before and passes after the fix. Link both CI runs.
- [ ] **Blocked PR**: a PR the pipeline correctly blocks (e.g. weakens an assertion so mutation drops, or breaks BR1).
      Keep it open/closed-unmerged with the red run linked.

## Leads (shared management)

- [ ] **Test plan + estimation** (`docs/team/test-plan.md`, `docs/team/estimation.md`): scope, risk-based approach, roles,
      environment, data, schedule, entry/exit/suspension/resumption criteria; three-point estimate per area, actual vs estimate at the end.
- [ ] **System & scope** final version (`docs/team/01-scope-draft.md` → finalize, verify every FR/BR against the running app).

## Your 2 use cases

- [ ] UC-A1 Moderator approves a pending booking, UC-A2 Moderator rejects a booking. Write them with the template and automate
      every flow in `tests/team/e2e/use-cases/` (see `area3-wania.md` for the framework).

## Viva prep

- [ ] Rerun one of your unit tests live and explain each assertion; explain MCC vs MC/DC for `can_cancel`;
      live task drill: "booking_limit_days is now exclusive (`<`)": predict the BR1 BVA test + mutation gate outcome.
