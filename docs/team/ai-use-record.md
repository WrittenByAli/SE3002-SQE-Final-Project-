# AI-Use Record

Required by the assignment (§7): tool, purpose, output, and what we checked or changed. Keep the prompts.

| # | Date | Member | Tool | Purpose | Output | What we checked / changed |
|---|---|---|---|---|---|---|
| 1 | 2026-11-21 | Ali | Claude Code (Claude Opus 5.5) | Read the assignment PDF and summarise the requirements | Summary of sections 1–7 and the rubric | _to fill: compared against the PDF_ |
| 2 | 2026-11-21 | Ali | Claude Code | Shortlist repos not already registered in Sections A–C; check the HTTP API and business-rule complexity | Recommendation: Indico Room Booking; source review of `rb` routes and rules | _to fill_ |
| 3 | 2026-11-21 | Ali | Claude Code | Draft scope (requirements, rules, roles) | `docs/team/01-scope-draft.md` | _to fill: verified each rule against source / app_ |
| 4 | 2026-11-21 | Ali | Claude Code | Local Docker setup, seed script, reset script, first API feasibility checks | `infra/`, `tests/team/seed/*`, `docs/team/02-local-setup-verification.md` | _to fill: re-ran reset.sh and the curl checks ourselves_ |
| 5 | 2026-11-21 | Ali | Claude Code | Repository structure: baseline import of v3.3.14, team scaffolding, rb source bind-mount | Baseline commit + team setup commit | _to fill_ |
| 6 | 2026-11-21 | Ali | Claude Code (Claude Opus 5.5) | Team harness (prerequisites only, no assignment deliverables): task division for 3 members, `CLAUDE.md`, 16 skills, 5 agents, loop recipes, guard hook, templates, GitHub workflow guide, PR/issue templates, CODEOWNERS, labels, branch protection, setup-only CI, Linux test runner, Playwright project scaffold, API fixtures, harness checker; pinned app versions | `.claude/`, `.github/`, `CLAUDE.md`, `docs/team/{tasks,harness,templates}/`, `infra/test-runner/`, `tests/team/{run.sh,tools,api,e2e}`, `infra/indico-containers/**` | _to fill by each member: read your task file + skills; confirm the split and the facts in them. Claude verified (automated): harness checker 9/9 + 7 injected violations caught; guard hook 15/15; app rebuilt with pinned versions + reset; Playwright login helper; CI run on the PR_ |
| 7 | 2026-11-21 | Ali | Claude Code | During harness verification a throwaway generated EP check found HTTP 500 for `repeat_frequency` DAY/WEEK/MONTH + `repeat_interval: 0` (finding 5 in `02-local-setup-verification.md`); the throwaway tests were deleted | Finding text only | _to fill: Fahima re-runs it herself before logging the Issue_ |

## Prompts

Keep the full prompt text or session exports here, or link to them (e.g. `docs/team/ai-prompts/`).
