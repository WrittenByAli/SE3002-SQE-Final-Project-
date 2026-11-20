---
name: sqe-defect
description: "Log, triage and analyse defects as GitHub Issues (severity, priority, status, triage decision), run 5 Whys + fishbone root cause analysis with corrective and preventive actions, and build the Pareto chart by category. Use for \"log a bug\", \"defect\", \"triage\", \"RCA\", \"5 whys\", \"fishbone\", \"pareto\"."
---

# Defect management & RCA (shared, lead Fahima, 7 marks)

## Log (same day you find it)
`gh issue create --template defect.yml` (or the GitHub web form "Defect"). Required: summary, steps, expected, actual, evidence
(test name + CI run / report path), severity, priority, area, risk ID. Labels used by the Pareto script:
`type:defect`, `severity:{critical,major,minor,trivial}`, `priority:{p1,p2,p3}`, `category:{validation,authorization,state,
error-handling,usability,accessibility,performance,security,documentation}`, `status:{new,triaged,in-progress,fixed,verified,reopened}`.

## Triage (weekly, all three)
Decision per issue: **fix** (owner + milestone) / **defer** (reason, residual risk) / **won't fix** (upstream behaviour, document) /
**duplicate** / **not a defect**. Record it as a comment `Triage: <decision> because <reason>` and update the labels.
Reopened? add `status:reopened` (feeds the reopen-rate metric).

## RCA (≥2 major defects) → `docs/team/defects.md` (template `docs/team/templates/rca.md`)
5 Whys down to a process/design cause (not "developer error"). Fishbone categories: Method, Machine (env), Material (data),
Measurement (tests/oracles), Man (skills), Milieu (requirements/docs). Then a corrective action (fix this one) + a preventive
action (stop the class of defect: new test type, gate, review rule).

## Pareto
Count open + closed defects by `category:*` label (`gh issue list --label type:defect --state all --json labels`), sort
descending, add the cumulative %, chart it, and keep the raw export + chart in `docs/team/evidence/shared/`. The vital few categories → where the next test effort goes.
