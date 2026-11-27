# Verified local application setup

Verified on 2026-11-27 in Fahima's Windows workspace. The local Indico stack is running at `http://localhost:8081`.

## Docker and environment file

Docker Desktop was available to the host shell:

- `docker version` reported Docker Desktop `4.92.0`, Engine `29.8.0`, `linux/amd64` (both Client and Server responded).
- `docker compose version` reported `Docker Compose version v5.5.1`.
- `git check-ignore -v infra/indico-containers/indico-prod/.env tests/team/.env.test` matched `.gitignore` lines 58 and 57 respectively. `git ls-files` returned neither path, so neither file is tracked. The contents of `.env` were not read or printed.

The `.env` file is ignored and must stay local. The reset script creates the ignored `tests/team/.env.test` containing the base URL, room ID, and synthetic API tokens; do not commit either file.

## Build and start

From the repository root in PowerShell, run the commands from the Indico Compose directory:

```powershell
Set-Location infra/indico-containers/indico-prod
docker compose build indico-web
docker compose build indico-celery indico-celery-beat
docker compose up -d
```

All three commands completed successfully. Docker reported `Image indico-prod-indico-web Built`, `Image indico-prod-indico-celery Built`, and `Image indico-prod-indico-celery-beat Built`; `docker compose up -d` reported the PostgreSQL, Redis, Celery, Celery beat, web, and nginx containers started.

`docker compose ps` then showed all six services `Up`; nginx publishes `0.0.0.0:8081->8080` and the web container publishes `0.0.0.0:9090->59999`. Authenticated timeline and booking API requests returned HTTP 200, verifying the app responded through the local nginx port. See [API curl evidence](evidence/room-timeline-user1-naive.txt) and [booking creation evidence](evidence/create-prebooking-user1-json.txt).

These are the commands verified in this workspace. Docker Desktop must be running before executing them. The initial image build downloads Indico and its font bundle and took several minutes; rebuilding later should use Docker's image cache unless inputs change.

## Seed data, admin, and test users

Run the repository's seed/reset script from the repository root. Git Bash is installed at the following path on this machine:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' tests/team/seed/reset.sh
```

This command completed successfully. Its output included:

```text
Waiting for Indico on http://localhost:8081 ...
Seeded: room_id=1 users={'admin': 1, 'user1': 2, 'mgr1': 3}
Wrote /d/SQE/finalproject/SE3002-SQE-Final-Project-/tests/team/.env.test
```

The script runs `docker compose down -v --remove-orphans`, starts the stack again, waits for Indico, and executes `tests/team/seed/seed_rb.py` in the web container. It creates a global admin (`admin`, `is_admin=True`), regular booker (`user1`), and room moderator (`mgr1`), plus room `R1` (ID 1). The room is public and reservable, requires confirmation, and has `booking_limit_days=7`; `mgr1` receives room-level `moderate` permission. The script creates `full:everything` API tokens for `user1` and `mgr1` and writes them to the ignored `.env.test` file. The seed output and subsequent API calls verified these records and roles are usable.

The seed source defines local-login passwords `admin-Pass123!`, `user1-Pass123!`, and `mgr1-Pass123!`. The seed command ran, but browser login was not needed for the API workflows and was not separately tested. If you want to inspect the admin UI manually, open `http://localhost:8081` and sign in as `admin` with `admin-Pass123!`. The seed does not create an admin API token; the current workflows use the `user1` and `mgr1` tokens.

No manual browser setup or screenshot is required for this API setup. The app is already running and the seed accounts are present.

## Reset

The same command is the verified reset-and-reseed procedure:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' tests/team/seed/reset.sh
```

It is destructive to this Compose project's database, Redis, and file volumes. A successful run recreates the demo records and overwrites `tests/team/.env.test` with newly generated tokens. It has been run successfully as shown above.
