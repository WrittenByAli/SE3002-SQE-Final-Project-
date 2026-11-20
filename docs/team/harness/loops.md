# Loop engineering: repeatable improvement loops

A loop = **measure → analyse → act → re-measure**, with an explicit stop condition so it never runs forever and never "games"
a metric. Run them with Claude Code's `/loop` (self-paced) or `/loop <interval>`. Each loop's prompt is below, so copy it as-is.
Every loop ends by logging AI use (`sqe-ai-log`) and never edits evidence or lowers a gate.

## L1: Coverage loop (Area 1)
Stop when: rule-surface statement **and** branch coverage = 100%, or the remaining lines are justified as unreachable.
```
/loop Run `bash tests/team/run.sh unit`. Read tests/team/reports/unit/rule-surface-coverage.md. If both totals are 100%, stop the
loop and summarise. Otherwise pick ONE function with missing lines/branches, explain to me which condition combination reaches
them, propose one test (I will review before you write it), add it to the right tests/team/unit file, and re-run. Never delete or
weaken existing assertions; never exclude code from coverage.
```

## L2: Mutation-kill loop (Area 1)
Stop when: every survivor is killed or classified equivalent with a proof, and score ≥ `mutation.score_min` final target.
```
/loop Run `bash tests/team/run.sh mutation`. Read tests/team/reports/mutation/survivors.md. If there are no unclassified survivors,
stop and summarise the score. Otherwise take the next 3 survivors, use the mutant-analyst agent for a first-pass verdict, show
me the verdicts, and for killable ones add the killing test. Append each verdict to docs/team/mutation-analysis.md marked
"PENDING member verification". Re-run.
```

## L3: CI watch (anyone with an open PR)
Stop when: the PR's checks are all green, or a failure needs a human decision.
```
/loop 10m Check `gh pr checks <PR>`. If all pass, stop. If a job failed, fetch its log with `gh run view --log-failed`, explain the
root cause in two sentences and propose the smallest fix. Do not push anything without my approval, and never add continue-on-error.
```

## L4: Weekly progress report (Fahima leads, Fridays)
Stop when: `docs/team/weekly/<date>.md` is written and reviewed.
```
/loop Collect this week's status: closed/open issues (gh issue list --state all --json ...), test counts per level, latest CI
run result, rule-surface coverage, mutation score, requirements coverage from docs/team/traceability.md. Fill
docs/team/templates/weekly-report.md into docs/team/weekly/<YYYY-MM-DD>.md with GQM metrics (defect density, requirements
coverage, reopen rate), plan-vs-actual and control actions. Every number must cite its source. Then stop.
```

## L5: Rubric audit (weekly, all)
```
/loop 7d Use the rubric-auditor agent. Post its gap table as a comment on the pinned "Rubric tracker" issue, then stop.
```

## L6: API case expansion (Area 2)
Stop when: every input of every in-scope endpoint has EP valid + all invalid classes + 3-point BVA cases executed.
```
/loop Regenerate cases (`python tests/team/generator/generate.py openapi/rb.yaml -o tests/team/generator/out/cases.json`), run
`bash tests/team/run.sh api`, list inputs that have no generated case or no executed test. If none, stop. Otherwise extend the
spec or generator for ONE input, regenerate, wire the cases into a parametrized test, re-run.
```

## Guardrails for all loops
- One small change per iteration; re-measure before the next.
- Never: lower thresholds, delete or skip tests, add `continue-on-error`/`|| true`, edit raw reports, or mark AI output as verified.
- If two iterations in a row make no progress, stop and ask the member.
