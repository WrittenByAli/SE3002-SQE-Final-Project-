# Test Plan: Indico Room Booking (v3.3.14)

> Assignment §2 "Test plan". Keep it updated: every change gets a row in the change log at the bottom.
> Source: `docs/team/01-scope-draft.md`. Verified behaviour: `docs/team/02-local-setup-verification.md`.

---

## 1. Scope

### In scope

| Item | Detail |
|---|---|
| System under test | Indico v3.3.14, **Room Booking module** (`indico/modules/rb`) only |
| Workflows | A: User creates a booking request (pre-booking, needs confirmation). B: Moderator approves, rejects, or user cancels. |
| Endpoints | `POST /rooms/api/booking/create`, `POST /rooms/api/bookings/<id>/{approve,reject,cancel}`, `GET /rooms/api/bookings/<id>`, `GET /rooms/api/rooms/<id>/timeline`, `POST /rooms/api/timeline` |
| Business rules | BR1 (boundary: past start, booking limit), BR2 (approve decision: pending ∧ can_moderate), BR3 (state machine: pending → accepted/rejected/cancelled), BR4 (permission: can_book / can_prebook) |
| Roles | `user1` (booker), `mgr1` (R1 moderator). `admin` = setup only, not tested. |
| Test levels | Unit (white-box, mutation), API (integration), E2E (Playwright + accessibility), Performance (k6) |
| Security | Access matrix verification (Playwright), OWASP ZAP passive scan, pip-audit |

### Out of scope

| Item | Reason |
|---|---|
| Recurring bookings | Complexity disproportionate to marks; single bookings cover all BR1–BR4 paths |
| Email notifications | Disabled in test env; no SMTP configured |
| Non-rb modules (events, registration, etc.) | Outside the assignment's chosen module |
| Upstream `indico/**/*_test.py` | Earn no marks (CLAUDE.md rule 8) |
| Browser compatibility (non-Chromium) | Playwright runs Chromium only; scope agreed in task division |

---

## 2. Approach by risk level

| Risk level | Risks (from register) | Techniques | Coverage target | Test levels |
|---|---|---|---|---|
| **High** | BR1 boundary off-by-one (booking limit), BR3 invalid state transition, role permission bypass (FR-A5, FR-B5) | BVA (3-point), state-transition table (all allowed + ≥1 disallowed per state), Playwright access checks, MCC/MC/DC on `can_cancel` | 100% stmt+branch on rule surface; mutation score ≥ 80% | Unit + API + E2E |
| **Medium** | Schema validation gaps (missing fields, wrong types), API error shape inconsistency, accessibility barriers | EP (valid/invalid classes per field), axe-core + Lighthouse scans | All invalid EP classes covered in API suite; 0 critical axe violations | API + E2E |
| **Low** | Performance degradation under load, dependency vulnerabilities, session cookie weaknesses | k6 (1 VU + 5 VU, 60 s measured), pip-audit, ZAP passive | p95 < 500 ms at 5 VU; 0 pip-audit critical CVEs | Performance + Security |

---

## 3. Roles

| Member | Area | Responsibilities | Reviews |
|---|---|---|---|
| **Muhammad Ali** (`WrittenByAli`) | Area 3: Use cases, a11y, security, performance | Use-case specs + Playwright automation (UC-A1, UC-A2), accessibility (Lighthouse, axe), access matrix, ZAP scan, pip-audit, k6, recovery test; **leads**: test plan, scope, risk register, completion report | Reviews Fahima's use cases; reviews Wania's PR |
| **Fahima** (`Fahima-sohail`) | Area 2: API + data generation | API/integration tests, OpenAPI spec, test-data generator; **leads**: traceability matrix, defect log, weekly reports | Reviews Ali's PR |
| **Wania** | Area 1: Static analysis, white-box, mutation, CI | SonarQube, CFG, unit tests (100% rule surface), MCC/MC/DC, mutmut, custom operators, CI quality gate; **leads**: test plan co-author (estimation + scope verification) | Reviews Fahima's PR |

---

## 4. Environment

| Item | Value |
|---|---|
| Host OS | Windows 11 Home, Docker Desktop 29.8.0 (WSL2) |
| App stack | nginx → uWSGI (Indico 3.3.14, PyPI), Celery + Redis, PostgreSQL 15 |
| Indico config | `BASE_URL=http://localhost:8081`, `DEFAULT_TIMEZONE=UTC`, `PLUGINS=set()`, `reservations_need_confirmation=True` for R1, `booking_limit_days=7` |
| Test runner (unit/mutation) | Linux container (`infra/test-runner/`): Python 3.12, Indico deps, mutmut 3.8.1, PostgreSQL 15 |
| E2E | Playwright (Chromium), `@axe-core/playwright`, Node 20 |
| Performance | k6 (host) |
| CI | GitHub Actions (`ubuntu-22.04`); see `.github/workflows/ci.yml` |
| Full details | `docs/team/02-local-setup-verification.md` |

---

## 5. Test data

- **Synthetic only.** No real users or personal data.
- Seed: `tests/team/seed/seed_rb.py` creates `admin`, `user1`, `mgr1`, location "SQE Campus", Room R1, API tokens.
- Reset: `bash tests/team/run.sh env-reset` wipes volumes and re-seeds. Run before each k6 session.
- Generated API test data: `tools/testgen/out/cases.json` (284 EP/BVA cases), `tools/testgen/out/decision_cases.json` (80 decision-table cases).
- Fixed future dates in all tests (never `datetime.now()` without control); UTC timezone throughout.

---

## 6. Schedule

| Week | Milestone | Ali | Fahima | Wania |
|---|---|---|---|---|
| W1 (now) | Foundation | Test plan, scope, risk register, UC specs (UC-A1, UC-A2) | — (Area 2 complete) | Sonar first run, CFG, MCC table |
| W2 | Test basis frozen | Access matrix, Lighthouse/axe baseline | Generator v1 regeneration demo | Rule surface locked, unit test skeleton |
| W3 | Bulk of tests | All UC flows automated, ZAP passive run | Full API suite from generator output | Unit tests to 100% rule surface, mutation baseline |
| W4 | Hardening | a11y fix before/after, k6 runs (1VU + 5VU), recovery test | Endpoint weaknesses report, traceability | Custom operators, kill survivors, gates at final values, fix PR + blocked PR |
| W5 | Report + viva prep | Completion report, risk residuals | Defects/Pareto final, traceability sign-off | Final CI evidence, mutation analysis report |

---

## 7. Criteria

| Type | Criterion (measurable) |
|---|---|
| **Entry** | App boots and seeds without error (`env-reset` exits 0). API tokens for user1 and mgr1 valid (curl checks in `02-local-setup-verification.md`). CI prerequisite jobs green on main. |
| **Exit — EC1** (functional, tied to R-01) | 100% statement + branch coverage of the rule surface (`tests/team/rule_surface.yml`). Mutation score ≥ 80% on the rule surface. |
| **Exit — EC2** (security, tied to R-05) | 0 critical or high axe violations on the two key workflow screens. No pip-audit critical CVEs in pinned `requirements.txt`. ZAP passive scan reviewed; ≥2 controls documented. |
| **Exit — EC3** (performance, tied to R-07) | p95 response time < 500 ms for the booking-create endpoint under 5 VU for 60 s. Error rate < 1%. |
| **Suspension** | App fails to seed (`env-reset` non-zero) or Docker stack crashes. Work on that environment; halt test runs until resolved. |
| **Resumption** | `env-reset` exits 0 and all CI prerequisite jobs green. |

---

## 8. Risks (summary — see full register at `docs/team/risk-register.md`)

Top risks: BR1 off-by-one (R-01, High), state-machine guard bypass (R-02, High), role permission bypass (R-03, High). Full 5×5 matrix and exit criteria linkage in the risk register.

---

## Change log

| Date | Change | By | Reason |
|---|---|---|---|
| 2026-11-28 | Initial version created | Muhammad Ali | Phase 1 foundation |
