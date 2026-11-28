# Report sections — Area 2 API testing

## Evidence basis and run identity

The latest completed **full API suite** recorded in the work session collected 382 tests and finished with **342 passed, 40 failed** in **201.06 seconds**. The suite included the generated cases, decisions, transitions, workflow checks, and four added coverage probes. Do not use the committed `docs/api/evidence/api-pytest-run.txt` as the raw transcript for that latest run: it belongs to an earlier 378-test run (341 passed, 37 failed, 401.97 seconds). The 382-test console output was returned in the Codex session but was not saved as a transcript. A later focused permission run collected four tests and returned **2 passed, 2 failed** before one unsupported HTML-content assertion was removed; that focused result is separate and was not folded into the full-suite totals. The removed assertion has not been rerun.

### (a) Techniques, test counts and results

| Technique / check | Tests in latest full run | Passed | Failed | Result notes |
|---|---:|---:|---:|---|
| Equivalence partitioning (EP) | 269 | 238 | 31 | Failures were generated cases, including malformed IDs, omitted timeline recurrence frequency, error-format header values, principal type/null and configured booking reason behavior. See the cases and explanations below and in `suspected-defects.md`. |
| Boundary value analysis (BVA) | 15 | 11 | 4 | Failed cases: `API-0006`, `API-0235`, `API-0248`, `API-0282`. The first three exercise malformed/below-minimum identifiers; `API-0282` exercises empty reject reason and reached HTTP 500. |
| Decision table | 80 | 80 | 0 | All generated combinations passed in the full run. Rule IDs are `BR1`, `BR2`, `BR3_REJECT`, `BR3_CANCEL`, `BR4_DIRECT`, and `BR4_PREBOOK`. |
| State transitions | 9 | 9 | 0 | All allowed transitions and selected disallowed transitions passed, including unchanged-state checks on rejected transitions. |
| Repeated requests | 2 | 0 | 2 | Identical sequential and rapid concurrent create requests each produced separate records. Duplicate prevention is a stated Area 2 test requirement, but an upstream idempotency guarantee was not found; disclose this test-basis assumption. |
| Cross-workflow | 1 | 1 | 0 | A booking created in workflow A was read and approved in workflow B; read-back confirmed the state change. |
| Existing lower-role checks | 2 | 2 | 0 | Booker denial of moderation and direct booking both passed. |
| Added coverage probes (not the above techniques) | 4 | 1 | 3 | Create with a missing room returned the expected 404. Two protected-room permission probes returned HTTP 200 rather than the asserted 403. The anonymous booking-detail probe followed the app's login redirect instead of returning the asserted 403. Later low-scope focused probes did observe 403 for all three read operations. |
| **Total** | **382** | **342** | **40** | This accounting sums to the full-suite result. The saved raw transcript is for the earlier 378-test run, not this run. |

The 31 EP and four BVA failures in this breakdown are counted by case IDs in the full-run output, with the 378-test saved transcript used to cross-check the generated-case classifications. The 382-test run added four coverage probes; do not claim its output is available as a committed raw log.

### (b) Traceability fragment

`docs/team/01-scope-draft.md` defines functional requirements `FR-A1` through `FR-B5`; it is explicitly marked as a draft, so the team should confirm those IDs and wording before submission. The mapping below uses those IDs alongside the business-rule IDs defined in `docs/api/context.md` and `tools/testgen/rules.yaml`.

| Test ID(s) | Requirement in project docs | Evidence/result in latest full run |
|---|---|---|
| `API-0001`–`API-0063` | Area 2 checklist: EP/BVA for every input and coverage criteria; Workflow A timeline query inputs. | 63 generated cases; results included in EP/BVA rows. |
| `API-0064`–`API-0130` | Area 2 checklist: EP/BVA for every input and coverage criteria; Workflow A multi-room timeline query inputs. | 67 generated cases; results included in EP/BVA rows. |
| `API-0131`–`API-0229` | `FR-A1` create booking, `FR-A2` reject past start, `FR-A3` booking limit, `FR-A4` pending/accepted outcome, `FR-A5` access; rules `BR1`, `BR4_DIRECT`, `BR4_PREBOOK`. | 99 generated cases; failures include explicit-null booked-for user, non-string principal, and empty/omitted reason under seeded `booking_reason_required=always`. |
| `API-0230`–`API-0242` | Workflow A shared-record/read-back and Area 2 EP/BVA/coverage criteria. | 13 generated cases; malformed booking identifiers returned 404 with `{}`. |
| `API-0243`–`API-0284` | `FR-B1` approval, `FR-B2` rejection, `FR-B3` nonpending approval refusal, `FR-B5` role denial; rules `BR2`, `BR3_REJECT`, `BR3_CANCEL`. | 42 generated cases; failures include malformed ID status mismatch, error-format header assumption, and empty reject reason returning 500. |
| `BR1-001`–`BR1-004` | `FR-A2`/`FR-A3`; `BR1`: start not in past and within booking limit. | 4 decision combinations; passed. |
| `BR2-001`–`BR2-004` | `FR-B1`/`FR-B3`/`FR-B5`; `BR2`: approval requires pending state and moderator permission. | 4 decision combinations; passed. |
| `BR3_REJECT-001`–`BR3_REJECT-008` | `BR3_REJECT`: terminal state, moderator permission, and reason presence. | 8 decision combinations; passed. |
| `BR3_CANCEL-001`–`BR3_CANCEL-032` | `BR3_CANCEL`: state, ownership/admin role, and cancellation grace period. | 32 decision combinations; passed. The docs flag some combinations as needing further live verification. |
| `BR4_DIRECT-001`–`BR4_DIRECT-016` | `FR-A5`; `BR4`: direct-book access by room reservability, visibility, confirmation setting and explicit permission. | 16 decision combinations; passed. |
| `BR4_PREBOOK-001`–`BR4_PREBOOK-016` | `FR-A4`/`FR-A5`; `BR4`: prebook access by room reservability, visibility, confirmation setting and explicit permission. | 16 decision combinations; passed. |
| `pending-to-accepted-approve`; `pending-to-rejected-reject`; `accepted-to-rejected-reject`; `pending-to-cancelled-cancel`; `accepted-to-cancelled-cancel`; `pending-to-denied-approve`; `accepted-to-denied-approve`; `rejected-to-denied-cancel`; `cancelled-to-denied-approve` | Area 2 checklist: every allowed transition plus a disallowed transition from each state; `BR2` and `BR3`. | 9 state-transition scenarios; passed. |
| `test_repeated_booking_requests_do_not_create_duplicates`; `test_rapid_concurrent_booking_requests_do_not_create_duplicates` | Area 2 checklist: repeated requests / no duplicate records. | Both failed; sequential IDs 161/162 and concurrent IDs 163/164 were distinct. Idempotency intent remains a test-basis assumption. |
| No separately named case identified | `FR-B4`: approving a colliding pre-booking is refused unless forced. | The reviewed test ID inventory does not show a dedicated collision scenario. Confirm and add one if this draft requirement remains in scope. |
| `test_workflow_b_reads_and_changes_workflow_a_record` | Shared record / cross-workflow visibility in Area 2 tasks and `docs/api/context.md`. | Passed; workflow B observed and changed the reservation created by workflow A. |
| `test_lower_privileged_role_cannot_moderate`; `test_lower_privileged_role_cannot_direct_book_confirmation_room` | `BR2`, `BR4`; Area 2 role checks. | Both passed. |

Generated ID ranges above describe the current baseline `cases.json`. They are generator IDs, not permanent requirement numbers; regeneration can shift later IDs. Functional requirement mappings come from the draft scope in `docs/team/01-scope-draft.md`; confirm that draft with the group before treating it as the final requirement catalogue.

### (c) Total and results by technique

In the latest completed full API suite, **382 tests ran: 342 passed and 40 failed**. EP contributed 269 tests (238 passed, 31 failed); BVA contributed 15 (11 passed, 4 failed); decision tables contributed 80 (80 passed); state transitions contributed 9 (9 passed); repeated requests contributed 2 (0 passed, 2 failed); cross-workflow contributed 1 (1 passed); existing lower-role checks contributed 2 (2 passed); and the added coverage probes contributed 4 (1 passed, 3 failed). These categories are mutually exclusive for the accounting table above.

The separate focused OAuth-scope run after that full suite had 4 selected API tests: 2 passed and 2 failed at an HTML expectation that was subsequently removed. Its assertions were not rerun after removal. Do not add these four tests to the 382-test total.

The prior saved transcript and `docs/api/suspected-defects.md` provide detailed request/response examples for the 378-test run. The most important findings carried into the later run were:

- Omitted `repeat_frequency` returned HTTP 500 (`Unexpected frequency NEVER`) on both timeline methods.
- A malformed principal JSON type (`user: 1`) returned HTTP 500 instead of a validation response.
- Empty reject reason returned HTTP 500 with a generic database-error body; read-back showed the reservation unchanged.
- Malformed booking-action identifiers returned 405 where the test basis expected 404.
- Identical create requests returned distinct booking IDs. The expected no-duplicate behavior is an assumption requiring product confirmation.
- Error-format header values were accepted on successful requests; this is a contract/test-basis mismatch because the header selects error representation rather than validating successful input.
- Empty/omitted create reason returned 422 under the seeded configuration where booking reason is required. Treat this as configuration-dependent, not a general defect.

### (d) Plain explanation of the generator

`tools/testgen/generate.py` reads `openapi/openapi.yaml`. It visits each documented operation and input: path, query and header parameters, request-body fields, and array item fields. It uses the schema type and constraints to choose representative valid values and invalid values.

Equivalence partitioning (EP) groups values expected to behave the same way. The generator creates valid examples for enum members and boolean choices, ordinary empty/non-empty values when allowed, and invalid examples such as a missing required field, wrong type, null, out-of-enum value, bad format, or value outside a declared limit. It aims to violate one constraint per invalid case. If it cannot produce an isolated sample, it stops rather than silently writing a misleading case. `$fixture` markers stand for values supplied by pytest fixtures, such as a real seeded room ID or collision-free time slot; they are not fake IDs or credentials.

Boundary value analysis (BVA) creates values immediately below, exactly at, and immediately above each explicit numeric, length, or item-count limit. `expected_valid` is based on the whole field schema, so a boundary point can still be invalid if it violates another constraint.

Decision cases come from `tools/testgen/rules.yaml`. For each rule, the generator forms every combination of listed conditions and finds the single matching outcome row. A missing or overlapping outcome is an error. These generated expectations describe the test basis; they are not proof of application behavior. Pytest consumes the generated case IDs and substitutes fixtures, sends requests to the running app, then checks the response and reads the shared reservation back.

The actual generator README is [tools/testgen/README.md](../../tools/testgen/README.md). It should be used as the implementation reference during a viva.

### (e) Finalized AI-use log

The canonical detailed log is [`docs/ai-use/fahima-ai-log.md`](../ai-use/fahima-ai-log.md), with the prompt texts in [`docs/ai-use/prompts/`](../ai-use/prompts/). The log records Codex as the tool and includes what was checked or changed. Report-ready summary:

| Prompt | Date | Purpose and recorded output |
|---|---|---|
| 001 | 2026-11-26 | Read assignment/repository context; established Area 2 scope and documented initial setup blockers. |
| 002 | 2026-11-27 | Verified Docker app setup and seed, inventoried workflow API endpoints, and saved live curl evidence. |
| 003 | 2026-11-27 | Wrote and validated the OpenAPI contract and recorded runtime differences. |
| 004 | 2026-11-27 | Built EP/BVA and decision-table generator; recorded 284 API cases and 80 decision cases plus generator test results. |
| 005 | 2026-11-27 | Added pytest API fixtures, generated-case loading, read-back helper and dependencies. |
| 006 | 2026-11-28 | Added API technique tests and recorded a full run of 341 passed / 37 failed from the saved 378-test transcript. |
| 007 | 2026-11-28 | Added HTTP logging and coverage analysis; recorded 1,741 exchanges and measured coverage, with final rerun limitations stated. |
| 008 | 2026-11-28 | Demonstrated temporary spec changes and regeneration; recorded that API testing could not start because Git Bash failed before pytest. |
| 009 | 2026-11-28 | Wrote evidence-based API weaknesses and ready-to-paste issues; marked duplicate prevention as an assumption. |
| 010 | 2026-11-28 | Prepared these report sections from recorded run outputs, docs and test IDs; listed submission checks below. |

### Verify these claims before submitting

1. **Confirm which full-run output is authoritative.** The 382-test, 342/40 result is from the later Codex console output and has no committed raw transcript. The saved evidence file is the earlier 378-test run at 341/37. Do not represent the earlier transcript as the raw record of the 382-test run.
2. **Re-run and save the final suite transcript** if the report must attach raw evidence for 382 tests. The run added four coverage probes, and one later focused assertion was removed but not rerun.
3. **Confirm the EP/BVA split of 238/31 and 11/4 against the exact full 382-test output** before quoting it; it is derived from matching generated IDs to the observed failure list, not from a separately archived JUnit report for that run.
4. **Confirm expected versus actual rule basis:** BR1–BR4 are based on the scope draft; some decision-table combinations in `rules.yaml` explicitly need more live verification.
5. **Confirm duplicate prevention is an intended requirement** with the team/product owner. Upstream docs/source did not establish an idempotency guarantee.
6. **Confirm the seeded configuration** for `booking_reason_required=always` before describing empty create-reason rejection as a defect.
7. **Confirm the draft FR catalogue with the team** and specifically verify that `FR-B4` collision rejection has a dedicated live API test if it remains in scope.
8. **Confirm the finalized AI log is acceptable to the instructor** and that the prompt files and shared team AI-use record requirements are both met. This workspace contains the Fahima-specific log and prompt archive under `docs/ai-use/`.
9. **Check whether each weakness has a GitHub issue** if your final report claims defects were formally logged. `docs/api/weaknesses.md` contains paste-ready issue text; those drafts are not themselves GitHub issues.
