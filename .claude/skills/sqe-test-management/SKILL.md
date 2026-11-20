---
name: sqe-test-management
description: "Shared test-management deliverables: test plan, three-point estimation, risk register (5x5), exit criteria, traceability matrix, weekly progress report with GQM metrics, test completion report with release/hold decision. Use for \"test plan\", \"risk register\", \"traceability\", \"weekly report\", \"GQM\", \"estimation\", \"completion report\", \"exit criteria\"."
---

# Test management (shared, 29 marks)

Templates in `docs/team/templates/`; leads in `docs/team/tasks/shared-test-management.md`.

## Risk register (lead: Wania)
Score = likelihood (1–5) × impact (1–5). Levels: 15–25 High, 8–14 Medium, 1–7 Low. **Level decides technique and depth**:
High → white-box MC/DC + mutation + API BVA + E2E; Medium → EP/BVA + decision table; Low → smoke only. ≥8 product + ≥2 project risks.
Every API/a11y/security/perf finding links back to a risk ID (R-xx).

## Exit criteria (≥3 measurable, ≥2 tied to the top risks), e.g.
- EC1 (R-01 BR1/BR3 wrong): rule-surface statement + branch coverage = 100% and mutation score ≥ 80%.
- EC2 (R-02 role bypass): 100% of access-matrix checks pass; 0 open High security defects.
- EC3 (perf): `booking/create` p95 ≤ 1500 ms at 5 VUs with < 1% unexpected failures.

## Estimation
Per area: O, M, P hours → E = (O+4M+P)/6, SD = (P−O)/6. Log actual hours weekly; final table actual vs E and the reasons for deviation.

## Traceability (lead: Fahima)
Rows = FR-/BR-; columns = unit tests, API tests, E2E/UC tests, result, defects. Requirements coverage = covered reqs / all reqs.
Generate test lists with `grep -rn "BR1\|FR-A1" tests/team` so the matrix matches real test names.

## Weekly report + GQM (lead: Fahima, every Friday)
Goal: assess readiness of Room Booking. Questions → Metrics:
defect density = defects / KLOC of rule surface; requirements coverage = covered / total; reopen rate = reopened / closed.
Compare to plan, then **control actions** (what you change next week because of the numbers). File: `docs/team/weekly/YYYY-MM-DD.md`.

## Test completion report (lead: Wania)
Tested / not tested (+why), deviations from plan, open defects, residual risk per risk ID, **release or hold** with
actual vs target for the 3 release (exit) criteria.
