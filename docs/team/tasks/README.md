# Team task division

This is the agreed division by testing area. **BR1–BR4 are shared requirements, not exclusive assignments:** each person tests the relevant rules through their own testing type, and all resulting tests map back to the same frozen Indico baseline. Every member owns two use cases and participates in shared test management.

## Area ownership

| Member | Area | Owned work | Task file |
|---|---|---|---|
| **Wania** (_GitHub username to add_) | **Area 1: Static analysis, white-box, mutation, and CI** | SonarQube metrics; hand-calculated cyclomatic complexity; unit tests; 100% scoped statement/branch coverage target; MCC/MC/DC; decision and state-transition tests; mutation testing; two custom operators; surviving-mutant analysis; GitHub Actions and coverage/mutation/Sonar gates | [wania-unit-mutation.md](wania-unit-mutation.md) |
| **Fahima** (`Fahima-sohail`) | **Area 2: API testing and data generation** | API/integration tests; OpenAPI; generated EP/BVA inputs; API coverage criteria; rejected requests and invalid transitions; repeated requests; shared-record read-back; endpoint findings | [fahima-api-quality.md](fahima-api-quality.md) |
| **Muhammad Ali** (`WrittenByAli`) | **Area 3: Use cases, usability, accessibility, security, and performance** | Shared Playwright framework and use-case template; browser use cases; usability tasks; Lighthouse/axe/keyboard; security access checks, passive ZAP, dependency audit, control review; k6 and recovery | [muhammad-ali-browser-security.md](muhammad-ali-browser-security.md) |
| **All three** | **Shared test management** | Test plan; three-point estimates; risk register and exit criteria; traceability; weekly progress; defect management and root-cause analysis; final completion report | [shared-test-management.md](shared-test-management.md) |

The team records three-point estimates and actual effort weekly. Rebalance supporting tasks if the estimates show a material workload difference.

## Rubric components

| Component | Ownership |
|---|---|
| System & scope | All three |
| Static analysis | Wania |
| Test plan | All three |
| Risk register | All three |
| White-box | Wania |
| API & integration | Fahima |
| Automated test data generation | Fahima |
| Use case spec | Every member writes their own |
| Use case automation | Every member automates their own; Ali owns shared framework |
| Mutation & CI | Wania |
| Usability & a11y | Ali |
| Defensive security | Ali |
| Performance & recovery | Ali |
| Defect management | All three |
| Monitoring & completion | All three |

## BR1–BR4 across test types

BR1–BR4 are project traceability IDs for rules implemented in Indico; they are not built-in system labels. Definitions and the cross-level matrix are in [the scope draft](../01-scope-draft.md). The division is by technique, so a rule may appear in unit, API, and browser tests:

- **BR1 — Booking start and length limit:** Wania covers it in unit tests; Fahima tests generated API partitions/boundaries; Ali covers the invalid-input/correction user flow.
- **BR2 — Approval eligibility:** Wania covers unit decisions; Fahima checks API role/state cases; Ali tests moderator approval and browser permissions.
- **BR3 — State transitions and cancellation permissions:** Wania covers unit/state cases and MCC/MC/DC for `Reservation.can_cancel`; Fahima tests API transitions; Ali tests the corresponding user/manager browser actions.
- **BR4 — Direct-book and pre-book permissions:** Wania covers unit cases; Fahima tests generated API permission cases; Ali checks role behavior in browser/security tests.

## Individual use cases

Every member writes and automates their own two use cases. Each includes preconditions, main flow, at least two alternative flows, at least two exception flows, postconditions, and FR/BR links; assert both the displayed result and postcondition.

| Member | Use case 1 | Use case 2 |
|---|---|---|
| Wania | User submits a request that violates a rule, corrects it, then succeeds | User checks booking status/timeline after a moderator decision |
| Fahima | User requests a room requiring confirmation | User cancels their own pending booking |
| Muhammad Ali | Moderator approves a pending booking | Moderator rejects a pending booking with a reason |

Ali owns the shared Playwright framework; every author owns their own use-case specification and tests. Review each other's specifications before finalizing automation.

## Shared test-management checklist

- **Test plan and estimation:** all three define the risk-based approach and estimate each area; record actual effort weekly and compare it with estimates.
- **System and scope:** all three verify the selected workflows, FR/BR IDs, rules, roles, and expected behavior against the running baseline.
- **Risk register and exit criteria:** all three identify/score risks, select test depth, and agree on at least three measurable exit criteria.
- **Traceability:** map every FR/BR to unit, API, and browser tests as applicable, results, and defects.
- **Defects and RCA:** every member reports defects from their area; all participate in Issue triage, two major RCAs, corrective/preventive actions, and Pareto analysis.
- **Weekly and completion reports:** all provide actual progress, GQM metrics, evidence, open defects, residual risks, and release/hold input.
- **Submission and viva:** each person owns their AI-use record, evidence, commits, and explanation of their area.

## Suggested sequence

| Week | Shared exit condition | Wania | Fahima | Muhammad Ali |
|---|---|---|---|---|
| W1 | Baseline and test basis confirmed; estimates recorded | Confirm rule surface; start unit suite and Sonar | Verify API; draft OpenAPI/generator plan | Establish Playwright framework and use-case specs |
| W2 | Test basis frozen | MCC/MC/DC for `Reservation.can_cancel`; coverage baseline | Generator v1 and initial API tests | Baseline usability/accessibility/security; choose performance limits |
| W3 | Core tests automated | Unit suite across BR1–BR4; mutation baseline | API suite and coverage report | Automate all six use cases; usability/security checks |
| W4 | Gates and evidence hardened | Two custom operators, surviving mutants, CI quality gates | Constraint-change demo; endpoint findings | A11y fix and before/after; k6 runs and recovery |
| W5 | Report and viva preparation | Final unit, mutation, Sonar, and CI evidence | Final API/generator evidence | Final UX/security/performance evidence |

Adjust dates to the course deadline. The sequence is a guide; the shared baseline and scope remain the same for all members.

## Working together

Read [the GitHub workflow](../harness/github-workflow.md): one task = one issue = one branch = one PR; `main` is protected and each PR requires a review and green `CI gate`. See the [harness map](../harness/README.md) and [templates](../templates/README.md).
