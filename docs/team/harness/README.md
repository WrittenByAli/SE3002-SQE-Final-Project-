# The SQE harness: what everything is and where to start

The harness is everything **around** the assignment work: environment, rules, task division, guides, templates, AI helpers,
review flow and CI. **No assignment deliverable exists yet.** Each member builds their own (see the task files).

## Start here (every member, ~30 minutes)

1. Read **[the task division](../tasks/README.md)**, then **your** task file:
   [Wania, Area 1](../tasks/area1-wania.md) · [Fahima, Area 2](../tasks/area2-fahima.md) ·
   [Muhammad Ali, Area 3](../tasks/area3-muhammad-ali.md) · [Shared test management](../tasks/shared-test-management.md)
2. Read **[how we work on GitHub](github-workflow.md)**: branches, PRs, reviews, CI. `main` is protected.
3. Set up your laptop: open Claude Code in the repo and say **"onboard me"** (skill `sqe-onboard`), or follow the steps in
   [`.claude/skills/sqe-onboard/SKILL.md`](../../../.claude/skills/sqe-onboard/SKILL.md).
4. Read the rules in [`CLAUDE.md`](../../../CLAUDE.md) (AI disclosure, no fabricated evidence, own your commits).

## Map

| Part | Where | What it gives you |
|---|---|---|
| Project rules + context for AI | [`CLAUDE.md`](../../../CLAUDE.md) | loaded into every Claude Code session: rules, ownership, system facts, commands |
| Task division | [`docs/team/tasks/`](../tasks/README.md) | who owns which rubric component, checklists, use-case split, week plan |
| GitHub workflow | [`github-workflow.md`](github-workflow.md) | branch names, PR flow, reviewer rotation, review checklist |
| Templates | [`docs/team/templates/`](../templates/README.md) | empty structures for every report the PDF needs |
| Skills (playbooks) | [`.claude/skills/`](../../../.claude/skills/) | 16 step-by-step guides, one per activity (say e.g. "use sqe-api-testing") |
| Agents (helpers) | [`.claude/agents/`](../../../.claude/agents/) | rubric-auditor, evidence-verifier, test-case-designer, mutant-analyst, viva-examiner |
| Loops | [`loops.md`](loops.md) | `/loop` recipes for coverage, mutation-kill, CI watch, weekly report, rubric audit |
| Guard hook | [`.claude/hooks/guard.py`](../../../.claude/hooks/guard.py) | blocks committing secrets, CI escape hatches, lowering gates, force-push to main |
| One command runner | [`tests/team/run.sh`](../../../tests/team/run.sh) | `env-up`, `env-reset`, `unit`, `mutation`, `api`, `e2e`, `perf`, `harness`, `shell` |
| App environment | [`infra/indico-containers/`](../../../infra/indico-containers/) | Indico 3.3.14 + PostgreSQL + Redis + nginx on :8081, pinned versions |
| Test runner | [`infra/test-runner/`](../../../infra/test-runner/) | Linux Python 3.12 + Indico deps + mutmut (needed on Windows) |
| Seed / reset | [`tests/team/seed/`](../../../tests/team/seed/) | synthetic users `user1`/`mgr1`/`admin`, room R1, API tokens → `tests/team/.env.test` |
| API test fixtures | [`tests/team/api/conftest.py`](../../../tests/team/api/conftest.py) | token clients, collision-free slots, payload builder (no tests yet) |
| Playwright project | [`tests/team/e2e/`](../../../tests/team/e2e/) | Chromium config, axe installed, login + API helpers (no tests yet) |
| CI | [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) | harness · runner · app-smoke → **CI gate** (required on every PR) |
| PR / issue templates | [`.github/`](../../../.github/) | PR checklist, Defect + Task forms, CODEOWNERS, labels |
| Harness self-check | [`tests/team/tools/check_harness.py`](../../../tests/team/tools/check_harness.py) | validates all of the above; runs in CI |

## Rules of thumb

- **Before you start a task:** open a Task issue, then create a branch, then load the skill for that activity.
- **Before you commit:** run the suite you touched, log AI use (`sqe-ai-log`), and never stage `.env*`.
- **Before you report a number:** make sure it came from a tool run you saved under `docs/team/evidence/` (`evidence-verifier`).
- **Every Friday:** weekly report (`sqe-test-management`) + rubric audit (`rubric-auditor`).
- **Before the viva:** `sqe-viva-prep` + `viva-examiner` until every component in your area is green.
