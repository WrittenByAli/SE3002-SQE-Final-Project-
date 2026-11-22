# Shared: Test management (29 marks, all three own the work)

Skill: `sqe-test-management`, `sqe-defect`. Agent: `rubric-auditor` (run weekly). Templates: `docs/team/templates/`.

| Component (marks) | Deliverable | Owners | Everyone's input |
|---|---|---|---|
| System & scope (5) | `docs/team/01-scope-draft.md` (final) | All three | verify FR/BR and rules against the app |
| Test plan, estimation, traceability (7) | `test-plan.md`, `estimation.md`, `traceability.md` | All three | agree on approach; each estimates and records actual hours; trace every applicable rule/test |
| Risk register & exit criteria (5) | `risk-register.md` | All three | identify risks, map techniques/depth, agree on measurable criteria |
| Defect management & RCA (7) | GitHub Issues + `defects.md` | All three | report and investigate area findings; triage, complete two major RCAs, and Pareto |
| Monitoring & completion (5) | `weekly/YYYY-MM-DD.md`, `test-completion-report.md` | All three | provide weekly GQM metrics, results, open defects, and residual risks |

## Checklist (assignment §2 "Test plan and test management")

- [ ] Test plan: scope, approach **by risk level**, roles, environment, test data, schedule, entry / exit / suspension / resumption criteria, risks. **Keep it updated** (change log at the bottom).
- [ ] Estimation: three-point (O, M, P → E = (O + 4M + P)/6) per area; actual effort logged weekly; compare at the end.
- [ ] Risk register: ≥8 product + ≥2 project risks; likelihood × impact (1–5) on a 5×5 matrix; risk level decides technique + depth.
- [ ] Exit criteria: ≥3, measurable (functional, performance, usability or security); ≥2 tied to the highest risks.
- [ ] Traceability matrix + requirements coverage %.
- [ ] Defects in GitHub Issues with severity, priority, status, triage decision; RCA (5 Whys + fishbone) for ≥2 major defects with corrective + preventive actions; Pareto by category; weaknesses linked to the risk register.
- [ ] Weekly progress report vs plan with control actions + GQM (defect density, requirements coverage, reopen rate).
- [ ] Test completion report: tested / not tested, deviations, open defects, residual risk per risk, release or hold.
- [ ] Final PDF: scope, risk register, traceability, results per activity, area ownership, AI-use record, evidence links,
      release/hold with actual vs target for 3 release criteria; every API/a11y/security/perf finding has root cause, severity, risk link, fix.
- [ ] Submission: `Project_<Roll1>_<Roll2>_<Roll3>_<Section>.zip` (with `.git`) + `.pdf`.
