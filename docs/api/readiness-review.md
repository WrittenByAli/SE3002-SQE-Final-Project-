# Area 2 readiness review

Reviewed against `SQE_Final_Project Fall 2026.pdf`, page 2 (API/integration and data generation), page 6 (Area 2 rubric), page 7 (AI disclosure), and `docs/team/tasks/area2-fahima.md`.

## Status

| Area 2 item | Current evidence | Status |
|---|---|---|
| OpenAPI description and API inventory | `openapi/openapi.yaml`, `docs/api/inventory.md`, `docs/api/spec-vs-actual.md`; five workflow operations are described and runtime differences are recorded. | Implemented; review whether assumptions match the team's final test basis. |
| OpenAPI-driven EP/BVA and decision generator | `tools/testgen/generate.py`, `rules.yaml`, README, generated JSON and generator tests. Baseline output: 284 API cases and 80 decision combinations. | Implemented and generator tests were run. |
| Spec-change demonstration | `docs/api/regeneration-demo.md`, baseline cases copy, and `docs/api/viva-cheatsheet.md`. Temporary changes regenerated 288 cases; spec and generated cases were restored. | Demonstrated generation. API tests for temporary constraints did not run because Git Bash failed before pytest; no live result is available. |
| API tests: EP/BVA, decisions, transitions, repeated requests, shared-record read-back, cross-workflow and roles | `tests/team/api/room_booking_api_test.py`; latest completed full run recorded in console: 382 tests, 342 passed, 40 failed. | Tests exist and real failures are documented. Not a clean passing suite. The committed raw transcript is from a previous 378-test run (341 passed, 37 failed), not the 382-test run. |
| API coverage criteria | `tools/api_coverage.py`, logger in `conftest.py`, `docs/api/coverage-report.md`. Its measured report comes from the earlier 378-test run. Some status/schema gaps remain; later focused probes were not incorporated into a final analyzer run. | Incomplete final verification. Re-run the suite and analyzer, save the exact output, and update the report. |
| Defects and endpoint weaknesses | `docs/api/suspected-defects.md`, `docs/api/weaknesses.md`. They document request, response, cause, severity/risk and fixes; duplicate prevention is marked as an assumption. | Findings documented; paste-ready drafts are not equivalent to GitHub defect Issues. Confirm the idempotency requirement and file/triage actual Issues. |
| Functional requirements and traceability | `docs/team/01-scope-draft.md` defines `FR-A1` through `FR-B5`, but labels itself a draft. The report traceability table now maps the API cases and business rules to those IDs. | Ask the team to confirm the draft catalogue. A dedicated live collision-approval test for `FR-B4` was not found in the reviewed test ID inventory; verify and add it if retained. |
| AI disclosure | `docs/ai-use/fahima-ai-log.md` and numbered prompts in `docs/ai-use/prompts/`. | Present in the Fahima-specific path. Confirm with the group/instructor whether the shared `docs/team/ai-use-record.md` must also be updated. |
| Reproducible setup and synthetic users | `docs/api/setup.md`; `.env` and `.env.test` are ignored. | Documented and previously run successfully; do not disclose or commit local secret files. |
| GitHub task and PR | Earlier AI log says task issue #11 was opened; current `gh auth status` reports an invalid token and GitHub API requests fail DNS resolution. No PR list could be retrieved in this audit. | Issue #11 existence is from prior recorded activity, not reverified today. PR status is unknown. The local branch has commits pushed previously, but current uncommitted work still needs commit/push. |

## What is not required right now

The assignment does not require screenshots for Area 2 API tests. Preserve raw pytest/curl/analyzer output and link it in the report. Screenshots may be relevant to Area 3's browser or Lighthouse work if that member chooses them, but they do not replace the required test reports.

## Keep these repository items

- `tools/testgen/out/cases.json` and `decision_cases.json`: generated test inputs, not accidental files.
- `docs/api/evidence/cases-before-regeneration-demo.json`: the requested before-copy for the spec-change demo.
- Local `infra/indico-containers/indico-prod/.env` and `tests/team/.env.test`: ignored, untracked local setup files. Do not delete them just to clean Git status and never commit them.
- `tests/team/reports/` and `__pycache__/`: ignored local run output/bytecode. They are not source deliverables and are not committed.

No upstream/application source or upstream tests were changed by Area 2. This review found no stray tracked secrets. The local `openapi/openapi.yaml` shows a status marker in Git, but `git diff -- openapi/openapi.yaml` is empty; verify with `git status` after the next Git refresh before interpreting that marker as a content change.

## Next actions before calling Area 2 complete

1. Re-run the full API suite and save its unedited output/JUnit file. Keep all real failures and update the defect/test-basis notes.
2. Run `python tools/api_coverage.py` against that run's HTTP log and update `docs/api/coverage-report.md` from the resulting output.
3. Decide with the team whether duplicate-create prevention is a product requirement; do not label it an upstream defect until confirmed.
4. Authenticate GitHub CLI, verify issue #11 and existing PRs, then open or update one PR from `test/a2-api-testing` against `main`. Link it with `Closes #11` only after confirming that issue is the right task.
5. Confirm the draft functional-requirement catalogue and add/verify a dedicated `FR-B4` collision test if it remains in scope.
6. Before submission, ensure defects requiring GitHub tracking have actual Issues, and reconcile the Fahima AI log with the shared AI-use record requirement.
