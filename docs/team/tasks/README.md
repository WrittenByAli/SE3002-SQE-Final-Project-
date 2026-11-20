# Task division: who does what

Assignment: 120 marks. Each member is **examined individually** on their area in the viva (20 marks: owned area,
live task, AI-use record). Any component you cannot explain can be set to zero, so own your area end to end.

## Ownership (assignment §6: one area per member; test management shared)

| Member | Area | Rubric components owned | Marks | Leads (shared) | Task file |
|---|---|---|---|---|---|
| **Muhammad Ali** (`WrittenByAli`) | 1: Static analysis, white-box, mutation, CI | Static analysis & metrics (5), White-box unit testing (16), Mutation & CI gate (8) | 29 | Test plan + estimation, System & scope | [area1-muhammad-ali.md](area1-muhammad-ali.md) |
| **Fahima** (`Fahima-sohail`) | 2: API testing & data generation | API & integration testing (10), Automated test data generation (7) | 17 | Traceability, Defect management + RCA, Weekly reports (GQM) | [area2-fahima.md](area2-fahima.md) |
| **Wania** (_GitHub: TBD_) | 3: Use cases, usability, accessibility, security, performance | Use case spec (3), Use case automation (6), Usability & a11y (5), Defensive security (6), Performance & recovery (5) | 25 | Risk register + exit criteria, Test completion report | [area3-wania.md](area3-wania.md) |
| **All three** | Test management | System & scope (5), Test plan/estimation/traceability (7), Risk register & exit criteria (5), Defects & RCA (7), Monitoring & completion (5) | 29 | the lead owns the document, everyone contributes | [shared-test-management.md](shared-test-management.md) |

Area 2 has fewer rubric marks, so Fahima leads three of the shared management components. That keeps the workload balanced.

## Everyone, individually (do not skip)

- **Two use cases per member** (assignment §2, "Two use cases per member"), each with ≥2 alternative and ≥2 exception
  flows, **automated in Playwright by the member who wrote them**. Wania owns the framework and the template. Suggested split:
  | Member | UC-1 | UC-2 |
  |---|---|---|
  | Muhammad Ali | UC-A1 Moderator approves a pending booking | UC-A2 Moderator rejects a booking (with reason) |
  | Fahima | UC-F1 User requests a room that needs confirmation | UC-F2 User cancels own pending booking |
  | Wania | UC-W1 User books with a rule violation, then corrects it (doubles as the usability task test) | UC-W2 User views booking status / timeline after a decision (keyboard-only test) |
- Commit your own work from **your own GitHub account** (history is checked in the viva).
- Log your AI use in `docs/team/ai-use-record.md`, with prompts kept in `docs/team/ai-prompts/<your-name>/`.
- Be able to **rerun one of your tests live** and explain every assertion.
- Prepare for the **live task**: a business-rule change or an updated API spec. Predict which tests and which CI gate
  fail, make the change, show the result (practise with the `sqe-viva-prep` skill and the `viva-examiner` agent).

## Timeline (set real dates once the deadline is known)

| Week | Goal (exit condition) | Ali | Fahima | Wania |
|---|---|---|---|---|
| W1 | **Registered + everyone runs the app** | register repo on the sheet, CI skeleton green, Sonar first run | run `env-reset` + `api` locally, draft OpenAPI for create/approve/reject | run `env-reset` + `e2e` locally, write UC template + own 2 UCs |
| W2 | **Test basis frozen** | CFG + hand CC, MCC table for `can_cancel` | generator v1 (EP + BVA from spec) | access matrix, Lighthouse/axe baseline |
| W3 | **Bulk of tests** | unit tests to 100% rule surface, mutation baseline | full API suite from generator output | all UC flows automated, ZAP passive run |
| W4 | **Hardening** | custom mutation operators, kill survivors, gates at final values, fix PR + blocked PR | 2 constraint changes + regeneration, endpoint weaknesses report | a11y fix before/after, k6 runs, recovery test |
| W5 | **Report + viva prep** | final metrics, CI evidence | traceability/defects/Pareto final | completion report, risk residuals |

Weekly: Friday progress report (Fahima leads) using `docs/team/templates/weekly-report.md`.

## How to work together

Read [the GitHub workflow](../harness/github-workflow.md): one task = one issue = one branch = one PR; `main` is protected;
every PR needs one approving review from another member (rotation: Ali → Fahima → Wania → Ali) and a green `CI gate`.
Map of the whole harness: [docs/team/harness/README.md](../harness/README.md). Templates: [docs/team/templates/](../templates/README.md).
