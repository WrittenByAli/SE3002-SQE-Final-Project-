---
name: sqe-onboard
description: "Start here. Onboards a team member to the SQE Indico project. Identifies who they are, sets up their machine, verifies the app/tests run, and shows their task checklist and next action. Use when a member opens a new session, says \"I'm Fahima/Wania/Ali\", \"what should I do\", \"where do I start\", or \"set up my laptop\"."
---

# SQE onboarding

## 1. Identify the member
Ask (if unknown): **Muhammad Ali** (Area 3), **Fahima** (Area 2) or **Wania** (Area 1)? Then read their task file:
- Ali → `docs/team/tasks/area3-muhammad-ali.md`
- Fahima → `docs/team/tasks/area2-fahima.md`
- Wania → `docs/team/tasks/area1-wania.md`
and `docs/team/tasks/shared-test-management.md` + `docs/team/tasks/README.md` (timeline, use-case split).

## 2. Machine setup (once), run in Git Bash on Windows
```bash
git clone https://github.com/WrittenByAli/SE3002-SQE-Final-Project-.git && cd SE3002-SQE-Final-Project-
git config user.name "<Full Name>"; git config user.email "<email used on GitHub>"   # commits must be yours
cp infra/indico-containers/indico-prod/.env.example infra/indico-containers/indico-prod/.env
#   edit .env: PGPASSWORD=<anything>, INDICO_SECRET_KEY=$(python -c "import secrets;print(secrets.token_hex(32))")
python -m venv .venv && .venv/Scripts/pip install -r tests/team/requirements-host.txt     # (Linux/mac: .venv/bin/pip)
bash tests/team/run.sh env-up       # first build 5–15 min
bash tests/team/run.sh env-reset    # ~1 min, writes tests/team/.env.test
PYTHON=.venv/Scripts/python bash tests/team/run.sh api   # expect: 4 passed
```
Area 1 (Wania) also: `bash tests/team/run.sh unit` (builds the Linux runner the first time). Area 3 (Ali) also: `bash tests/team/run.sh e2e`.
Port 8081 busy? Change `NGINX_PORT` in `.env` **and** `BASE_URL` in `indico.conf`. Use the `sqe-env` skill for troubleshooting.

## 3. Show status + next action
- Read the member's checklist; list unchecked items for the current week (timeline in `tasks/README.md`).
- Check open GitHub Issues assigned to them: `gh issue list --assignee @me`.
- Propose **one** concrete next step, and name the skill to use for it.

## 4. Remind the rules (CLAUDE.md)
Own your work, commit from your account, log AI use (`sqe-ai-log`), never fabricate evidence, no CI escape hatches.
