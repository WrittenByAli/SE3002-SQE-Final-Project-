# Area 3: Muhammad Ali: Use cases, usability, accessibility, security, performance (25 marks + leads)

Skills: `sqe-use-cases`, `sqe-a11y`, `sqe-security`, `sqe-performance`. Agents: `evidence-verifier`, `viva-examiner`.
Commands: `bash tests/team/run.sh env-reset`, `bash tests/team/run.sh e2e`, `bash tests/team/run.sh perf`.
Test accounts: `user1` / `mgr1` (password `<username>-Pass123!`), app at http://localhost:8081.

## 1. Use case specification (3 marks) + automation (6 marks)

- [ ] Own the **use-case template** (`docs/team/templates/use-case.md`) and the Playwright framework (`tests/team/e2e/`).
- [ ] Every member writes **2 use cases** (see the split in `docs/team/tasks/README.md`), each with preconditions, main flow,
      **≥2 alternative + ≥2 exception flows**, and postconditions, derived from the requirements (FR-/BR- IDs). → `docs/team/use-cases/`
- [ ] **Automate every flow in Playwright (Chromium)**: assert the result shown **and** the postconditions (read back via API
      or UI). The Playwright project (`tests/team/e2e/`: config, Chromium, axe, login helper) is set up and ready; tests go in `tests/team/e2e/tests/`. Your own: UC-A1, UC-A2.
- [ ] Review the other members' use cases for completeness before they automate them.

## 2. Usability & accessibility (5 marks)

- [ ] **Two task tests**, one per workflow: open the task screen, complete the task, assert the confirmation.
      In one of them first submit a value the business rule rejects, check that the error explains what to correct, then correct it and succeed.
- [ ] In one test, **keyboard-only navigation**: assert focus order reaches the required fields + submit, and the keyboard submits.
- [ ] **Lighthouse** (accessibility, best practices, SEO) on each use case's key screen (logged in), plus a full
      **axe-core** scan via `@axe-core/playwright`. Count an issue found by both tools once. For each issue: element,
      user impact, proposed fix. → `docs/team/accessibility.md`
- [ ] **Fix one screen** (in the MIS, or your own HTML page), rerun both tools, compare before and after. Keep both raw reports in
      `docs/team/evidence/area3/`.

## 3. Defensive security (6 marks)

- [ ] Routes + data of both workflows, and an **access matrix** (role × action → expected). → `docs/team/security.md`
- [ ] **Playwright checks of ≥4 access decisions across both roles** (≥1 allowed, ≥1 denied); record role, action,
      expected, observed, evidence (the role behaviour verified so far is in `docs/team/02-local-setup-verification.md`).
- [ ] **OWASP ZAP passive scan** while the Playwright tests run both workflows (proxy Playwright through ZAP).
      Review ≥2 controls (session cookie attributes, role checks, CSRF), and back them up with source/config.
- [ ] **Dependency audit** (`pip-audit` on the pinned `requirements.txt`): record packages + versions checked; for each finding:
      component, evidence, likely impact, correction. No findings? Document the verified controls instead.

## 4. Performance & recovery (5 marks)

- [ ] Pick one operation (recommended: `GET /rooms/api/rooms/{id}/timeline` or `POST booking/create`), and **before testing**
      set p95 and error-rate limits with a justification.
- [ ] **k6**: 1 VU, then ≥5 VUs; **each setup twice**, ≥60 s measured after ramp-up, same build/machine/data
      (`env-reset` before each run). Report p95 ms, req/s, % unexpected failures per run vs limits. Write the script in `tests/team/perf/`; run it with `bash tests/team/run.sh perf <script>.js`.
- [ ] **Failure-and-recovery test** for a state-changing operation: dependency unavailable before the write completes
      (e.g. stop PostgreSQL / use a test double), verify persisted state, restore, retry, assert final state **without duplicates**.
      → `tests/team/perf/recovery_test.py`, results in `docs/team/performance.md`

## Leads (shared management)

- [ ] **Risk register**: ≥8 product + ≥2 project risks, likelihood × impact on a 5×5 matrix, each mapped to technique and depth;
      **≥3 measurable exit criteria**, ≥2 tied to the highest risks (`docs/team/risk-register.md`).
- [ ] **Test completion report**: tested / not tested, deviations, open defects, residual risk per risk, release/hold
      recommendation with actual vs target for the 3 release criteria (`docs/team/test-completion-report.md`).

## Viva prep

- [ ] Rerun the keyboard test live and explain each focus assertion; explain why an issue counted once across Lighthouse+axe;
      explain the p95 limit you chose.

