# CLAUDE.md: SE3002 SQE Final Project harness

You are working in a **university group project**: automated quality engineering of the open-source MIS
**Indico** (Room Booking module) for SE3002 Software Quality Engineering, Fall 2026. Grading includes a viva
in which every member must explain their own work. These rules exist so that AI help never costs the team marks.

## Non-negotiable rules (academic integrity, assignment §7)

1. **Log every AI-assisted change.** Each session that produces code, tests, docs or analysis that gets committed must
   add a row to `docs/team/ai-use-record.md` (tool, purpose, output, what the member checked or changed). Remind
   the member before they commit. Use the `sqe-ai-log` skill.
2. **Never fabricate or edit evidence.** Reports, screenshots, pipeline runs, coverage, mutation scores, Lighthouse/axe/ZAP/k6
   output must come from real runs. Never type numbers into a report that a tool did not produce. Cite the artifact path.
3. **The member owns the work.** Explain what you generate so they can defend it in the viva. Prefer guiding the
   member through a task (questions, tables, review) over writing finished deliverables for them. Each member commits
   their own work from their own GitHub account. Never commit for someone else.
4. **No escape hatches in CI**: no `continue-on-error`, `|| true`, `--exit-zero`, `set +e`, skipped or xfail'd tests used to make
   a gate pass, and `if: always()` only on the `CI gate` aggregator (which fails unless every job succeeded).
   `tests/team/tools/check_harness.py` enforces this on every PR.
5. **Never lower a quality gate** in `tests/team/quality-gates.yml` without a written justification in the PR.
6. **Secrets stay out of git**: `tests/team/.env.test`, `infra/indico-containers/indico-prod/.env`. A PreToolUse hook
   blocks commits that contain them.
7. **Nobody pushes to `main`.** Branch → PR → 1 approving review from another member + green `CI gate` → merge.
   Follow `docs/team/harness/github-workflow.md` (branch names, reviewer rotation, review checklist).
8. **Upstream code changes only through PRs** with a linked GitHub Issue (defect fix, the documented fix PR, the blocked PR,
   the viva live task). Upstream tests (`indico/**/*_test.py`) earn no marks. Team tests live in `tests/team/`.

## Team and ownership

| Member | GitHub | Area (examined on it in the viva) | Task file |
|---|---|---|---|
| Muhammad Ali | `WrittenByAli` | **Area 1**: SonarQube + cyclomatic complexity, white-box unit tests (100% stmt/branch, MCC, MC/DC), mutation testing, CI quality gate | `docs/team/tasks/area1-muhammad-ali.md` |
| Fahima | `Fahima-sohail` | **Area 2**: API and integration testing (EP, 3-point BVA, decision tables, state transitions, read-back), OpenAPI spec + test-data generator | `docs/team/tasks/area2-fahima.md` |
| Wania | _(add GitHub username)_ | **Area 3**: use cases + Playwright automation, usability and accessibility (Lighthouse, axe, keyboard), defensive security (access matrix, ZAP passive, pip-audit), performance (k6) + recovery | `docs/team/tasks/area3-wania.md` |
| All three | | **Test management**: plan, estimation, risk register, traceability, defects + RCA, weekly reports, completion report | `docs/team/tasks/shared-test-management.md` |

When a member starts a session, ask who they are if it is unclear, then load their task file and work from its checklist.

## System under test

- Upstream https://github.com/indico/indico, tag `v3.3.14`, commit `a42252ead3509f9b31db0691cc9af899ab18416e` (MIT).
  The repo's first commit is that baseline, unmodified.
- Module: **Room Booking** `indico/modules/rb`. Workflow A: user requests a room that needs confirmation (pending).
  Workflow B: room moderator approves/rejects. Shared record: the `Reservation` + slot availability.
- Candidate business-rule surface (Area 1 fixes the final list in `tests/team/rule_surface.yml`; coverage/mutation gates measure only it):
  BR1 boundary (booking length ≤ `booking_limit_days`, start not in past), BR2 decision (`can_accept` = pending ∧ can_moderate),
  BR3 state (pending→accepted/rejected/cancelled, guards in `RHBookingStateActions._check_access`; **critical module** =
  `Reservation.can_cancel` for MCC + MC/DC), BR4 permission (`Room.can_book` / `can_prebook`).
- Roles: `user1` (booker: can pre-book R1, cannot approve) and `mgr1` (R1 moderator: approve/reject). `admin` = setup only.
- Full scope: `docs/team/01-scope-draft.md`. Verified behaviour + known findings: `docs/team/02-local-setup-verification.md`.

## Commands (all via `tests/team/run.sh`)

```bash
bash tests/team/run.sh env-up      # app stack (Docker) -> http://localhost:8081
bash tests/team/run.sh env-reset   # wipe + seed (~1 min); writes tests/team/.env.test (tokens, room id)
bash tests/team/run.sh unit        # tests/team/unit + coverage json/xml/html (Linux container: Py3.12 + Postgres)
bash tests/team/run.sh mutation    # mutmut, args passed through (Linux container)
bash tests/team/run.sh api         # API tests vs running app (host Python, tests/team/requirements-host.txt)
bash tests/team/run.sh e2e         # Playwright (Chromium) + axe vs running app
bash tests/team/run.sh perf x.js   # k6 script from tests/team/perf/
bash tests/team/run.sh harness     # validate this harness (skills, agents, workflows, links, gates)
```

Windows: run from **Git Bash**. Unit/mutation always run in the Linux container (Indico needs Python 3.12; mutmut needs Linux).
App code changes in `indico/modules/rb` take effect after `docker compose restart indico-web indico-celery`
(run in `infra/indico-containers/indico-prod`), because that folder is bind-mounted into the container.

## Project status

**Prerequisites are done; the assignment work itself has not started.** Ready: pinned app stack + seed/reset, Linux test runner
(Py3.12, Indico deps, mutmut), API test fixtures, Playwright project, CI prerequisite jobs + branch protection, this harness.
Every deliverable (tests, spec, generator, gates, reports) is built by its owner. See `docs/team/tasks/`.

## Where things go

| What | Where |
|---|---|
| Unit tests (`*_test.py`) | `tests/team/unit/` |
| API/integration tests | `tests/team/api/` |
| OpenAPI spec | `openapi/rb.yaml` |
| Test-data generator + output | `tests/team/generator/` (output `tests/team/generator/out/`, committed) |
| Playwright tests, axe | `tests/team/e2e/` |
| k6 scripts, recovery test | `tests/team/perf/` |
| Security checks | `tests/team/e2e/security/` (Playwright access matrix), `docs/team/security/` |
| Gate config (Area 1 creates) | `tests/team/quality-gates.yml`, `tests/team/rule_surface.yml` |
| Test management + reports | `docs/team/` (templates in `docs/team/templates/`) |
| Evidence (tool output) | `docs/team/evidence/<area>/<date>-<what>/` (raw files, never edited) |

## Skills, agents, loops

- Skills (`.claude/skills/`): `sqe-onboard` (start here), `sqe-env`, `sqe-ai-log`, `sqe-whitebox`, `sqe-mutation`,
  `sqe-ci-gate`, `sqe-sonar`, `sqe-api-testing`, `sqe-openapi-generator`, `sqe-use-cases`, `sqe-a11y`, `sqe-security`,
  `sqe-performance`, `sqe-test-management`, `sqe-defect`, `sqe-viva-prep`.
- Agents (`.claude/agents/`): `rubric-auditor` (gap report vs the marking rubric), `evidence-verifier`
  (are claims backed by real artifacts?), `test-case-designer` (EP/BVA/decision/state tables from a rule),
  `mutant-analyst` (classify surviving mutants), `viva-examiner` (mock viva questions on a member's area).
- Loops: `docs/team/harness/loops.md` (`/loop` recipes: mutation-kill loop, coverage loop, CI watch, weekly report).

## Style

- Tests: one behaviour per test, the technique and rule ID in the test name or docstring (e.g. `BR1 BVA just above`),
  assert status **and** body **and** read-back state. Fixed dates in the future, never "now" without control.
- Docs: tables over prose; every number cites the artifact it came from.
- Commits: imperative subject, reference the issue (`Fixes #12`), small and owned by one member.
