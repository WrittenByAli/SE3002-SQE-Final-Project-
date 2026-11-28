# Risk Register: Indico Room Booking (v3.3.14)

> Owner: Muhammad Ali (Area 3). Updated: 2026-11-28.
> Score = Likelihood (1–5) × Impact (1–5). Level: 15–25 High · 8–14 Medium · 1–7 Low.
> Required: ≥8 product risks + ≥2 project risks. The level decides technique and depth.

---

## Risk table

| ID | Type | Risk | L | I | Score | Level | Technique(s) | Depth | Owner | Linked tests / findings | Residual |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R-01 | product | BR1 boundary off-by-one: booking_limit_days comparison uses `<` instead of `<=` (or vice-versa), allowing or blocking bookings by 1 day | 4 | 5 | 20 | **High** | BVA 3-point (6/7/8 days); mutation operator `<=`→`<` | Full BVA suite + custom mutant; mutation gate | Wania (unit), Ali (UC-A1) | UC-A1 A1 flow; API test `BR1_BVA_*` | — |
| R-02 | product | BR3 invalid state transition: a terminal booking (rejected/cancelled) can be re-approved or re-rejected due to missing guard | 3 | 5 | 15 | **High** | State-transition table (all allowed + ≥1 disallowed per state) | Full transition matrix; unit + API tests | Wania (unit), Fahima (API) | API: `approve-already-approved`, `approve-rejected`; `02-local-setup-verification.md` checks 7, 12 | — |
| R-03 | product | Role permission bypass: a non-moderator user can call approve/reject due to missing or incorrect `can_moderate` check | 3 | 5 | 15 | **High** | Playwright access matrix (≥4 decisions); API EP invalid-role class | Full access matrix; FR-B5 unit test | Ali (Playwright), Fahima (API) | Playwright access check; API `FR-A5`, `FR-B5` | — |
| R-04 | product | Schema validation gap: required fields (reason, room_id, start_dt) accepted silently when missing, creating malformed reservations | 3 | 4 | 12 | **Medium** | EP invalid classes (missing required, wrong type, negative interval); API suite | All invalid EP classes covered | Fahima (API) | API tests `missing_fields`, `missing_reason`; `02-local-setup-verification.md` check 10 | — |
| R-05 | product | Accessibility barrier: key booking UI screens have critical axe violations (missing labels, focus traps, contrast failures) that prevent keyboard-only use | 3 | 4 | 12 | **Medium** | axe-core scan + Lighthouse audit; keyboard-only Playwright test | Scan both workflow screens; fix ≥1 violation | Ali (E2E / a11y) | UC-A2 E1/E2; `docs/team/accessibility.md` | — |
| R-06 | product | Cross-workflow conflict not enforced: after approval, the same slot can be double-booked because the conflict check is skipped | 3 | 4 | 12 | **Medium** | API read-back (cross-workflow test after approve); state-transition post-condition | Full read-back after each state change | Fahima (API), Ali (UC-A2) | `02-local-setup-verification.md` check 9; API `cross_workflow` | — |
| R-07 | product | Performance degradation: booking-create endpoint exceeds p95 500 ms under 5 concurrent users, blocking usability | 2 | 4 | 8 | **Medium** | k6 load test (1 VU + 5 VU, 60 s measured, 2 runs each) | Measured p95 + req/s + error rate vs limits set before run | Ali (perf) | `tests/team/perf/`; `docs/team/performance.md` | — |
| R-08 | product | Dependency vulnerability: a known CVE in a pinned dependency (Flask, SQLAlchemy, Pillow, etc.) exploitable in the deployment context | 2 | 4 | 8 | **Medium** | pip-audit on `requirements.txt` | Report all findings; document controls or correction | Ali (security) | `docs/team/security.md`; pip-audit output in evidence | — |
| R-09 | product | CSRF / session misconfiguration: session cookies lack `HttpOnly` or `SameSite`, or CSRF token is not enforced on state-changing endpoints | 2 | 3 | 6 | **Low** | ZAP passive scan (proxy Playwright through ZAP); source review (`indico/web/rh.py`) | ≥2 controls reviewed and documented | Ali (security) | ZAP report; `docs/team/security.md` | — |
| R-10 | product | Recovery failure: a PostgreSQL outage during booking creation leaves the reservation in a partial or duplicate state after restart | 2 | 4 | 8 | **Medium** | Failure-and-recovery test (stop Postgres mid-write, verify state, restore, retry) | Assert no duplicate; assert final state matches expected | Ali (perf) | `tests/team/perf/recovery_test.py`; `docs/team/performance.md` | — |
| R-11 | project | Docker / environment setup failure: team member cannot run `env-reset` due to WSL2 or port conflict, blocking local testing | 3 | 3 | 9 | **Medium** | Pre-flight check (`sqe-env` skill); documented port override (`NGINX_PORT`) | Documented workaround in `02-local-setup-verification.md` | All | `docs/team/02-local-setup-verification.md` | — |
| R-12 | project | Branch-protection / review bottleneck: sole reviewer unavailable delays PR merge, blocking dependent work in CI | 2 | 3 | 6 | **Low** | Review rotation (Ali→Fahima→Wania→Ali); auto-merge enabled on green CI | Reviewer responds within 24 h | All | `docs/team/harness/github-workflow.md` | — |

---

## 5 × 5 matrix

Rows = Likelihood (5 = almost certain, 1 = rare). Columns = Impact (1 = negligible, 5 = critical).

| L \ I | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | | | | | |
| **4** | | | | | R-01 |
| **3** | | | R-09 | R-04, R-05, R-06 | R-02, R-03 |
| **2** | | | R-12 | R-07, R-08, R-10 | |
| **1** | | | | | |

---

## Exit criteria

| ID | Criterion (metric, threshold) | Linked risk(s) | Measured by (artifact) |
|---|---|---|---|
| EC1 | 100% statement + branch coverage of the rule surface; mutation score ≥ 80% | R-01, R-02 | `tests/team/quality-gates.yml`; coverage JSON + mutmut run |
| EC2 | 0 critical or high axe violations on both workflow screens; 0 pip-audit critical CVEs | R-05, R-08 | axe report in `docs/team/evidence/area3/`; pip-audit output |
| EC3 | p95 < 500 ms and error rate < 1% for booking-create under 5 VU for 60 s | R-07 | k6 summary in `docs/team/performance.md` |
