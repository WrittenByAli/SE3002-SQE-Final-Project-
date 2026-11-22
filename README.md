# SE3002 SQE Final Project: Automated Testing of Indico Room Booking

Automated quality engineering of an open-source MIS for SE3002 Software Quality Engineering (Fall 2026).

## System under test

| | |
|---|---|
| MIS | **Indico**: open-source event and room-booking management system (CERN) |
| Upstream | https://github.com/indico/indico |
| Baseline | tag **`v3.3.14`**, commit **`a42252ead3509f9b31db0691cc9af899ab18416e`** (imported unmodified as this repo's first commit) |
| Licence | MIT (see [LICENSE](LICENSE)) |
| Module | Room Booking (`indico/modules/rb`) |
| Workflow A | User submits a booking request for a room that needs confirmation, which creates a **pending** booking |
| Workflow B | Room manager **approves / rejects** it (pending → accepted / rejected / cancelled) |
| Shared record | the `Reservation` and the room's availability for that slot |

Scope, requirements, business rules and roles: [docs/team/01-scope-draft.md](docs/team/01-scope-draft.md)
Local setup evidence and first API results: [docs/team/02-local-setup-verification.md](docs/team/02-local-setup-verification.md)

## Repository layout

| Path | Contents |
|---|---|
| `indico/`, root files | Upstream Indico source at the baseline. Changes to it go only through PRs |
| `tests/team/` | **All team tests** (upstream `*_test.py` files are not ours and earn no marks) |
| `tests/team/seed/` | `seed_rb.py` (synthetic data) and `reset.sh` (full wipe + reseed) |
| `infra/indico-containers/` | Docker setup, adapted from [indico/indico-containers](https://github.com/indico/indico-containers) @ `5ebc1f3` |
| `docs/team/` | Task division, harness guides, templates, (later) test plan, risk register, traceability, reports |
| `infra/test-runner/` | Linux runner (Python 3.12, Indico deps, mutmut) for unit + mutation testing |
| `.claude/` | Claude Code harness: skills, agents, guard hook, settings |
| `.github/` | CI workflow, PR template, issue forms, CODEOWNERS, labels, branch protection |

## Setup

Requirements: Docker Desktop (or Docker Engine + Compose v2), Git, Python 3.11+, curl, bash (Git Bash on Windows).

```bash
cd infra/indico-containers/indico-prod
cp .env.example .env          # then set PGPASSWORD and INDICO_SECRET_KEY
docker compose up -d --build  # first build ~5–10 min; Indico at http://localhost:8081
cd ../../..
bash tests/team/seed/reset.sh # wipe + seed; writes tests/team/.env.test (tokens, room id)
```

The containers run Indico 3.3.14 from PyPI, but **`indico/modules/rb` is bind-mounted from this repo**. After changing
room-booking code, run `docker compose restart indico-web indico-celery` (in `infra/indico-containers/indico-prod`).

Test accounts (synthetic): `admin`, `user1` (booker), `mgr1` (R1 moderator). Password is `<username>-Pass123!`.

### Reset between runs

```bash
bash tests/team/seed/reset.sh   # drops all volumes (DB, Redis, files), recreates schema, reseeds (~1 min)
```

### Stop

```bash
cd infra/indico-containers/indico-prod && docker compose down      # keep data
docker compose down -v                                             # also wipe data
```

## Team and area ownership

| Member | Area | Task file |
|---|---|---|
| Wania | Area 1: static analysis, white-box, mutation, and CI | [wania-unit-mutation.md](docs/team/tasks/wania-unit-mutation.md) |
| Fahima (`Fahima-sohail`) | Area 2: API testing and data generation | [fahima-api-quality.md](docs/team/tasks/fahima-api-quality.md) |
| Muhammad Ali (`WrittenByAli`) | Area 3: use cases, usability, accessibility, security, and performance | [muhammad-ali-browser-security.md](docs/team/tasks/muhammad-ali-browser-security.md) |
| All three | Test management (leads per component) | [shared-test-management.md](docs/team/tasks/shared-test-management.md) |

## Start here (new member)

1. [Task division](docs/team/tasks/README.md) → your task file.
2. [How we work on GitHub](docs/team/harness/github-workflow.md): `main` is protected; branch → PR → review → merge.
3. [Harness map](docs/team/harness/README.md): skills, agents, templates, CI, commands.
4. In Claude Code, say **"onboard me"**. [`CLAUDE.md`](CLAUDE.md) holds the project rules every session follows.

Status: **prerequisites and harness done; assignment work not started.** All team commands: `bash tests/team/run.sh help`.

## AI use

Generative AI (Claude Code) was used for repository selection research, scope drafting, environment setup and the seed and reset
scripts. All of it is recorded in `docs/team/ai-use-record.md` with prompts, outputs and what the team checked or changed.
