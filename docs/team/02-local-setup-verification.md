# Local Setup and API Feasibility Check (2026-11-21)

> Run by Claude Code (AI-assisted) on the team laptop. Record this in the AI-use record. All data is synthetic.
> Re-run it yourselves before registering: `bash tests/team/seed/reset.sh`, then the curl checks below.

## Environment

| Item | Value |
|---|---|
| Host | Windows 11 Home, Docker Desktop 29.8.0 (WSL2 backend) |
| Indico | **3.3.14** (PyPI, built by `infra/indico-containers/indico-prod/worker/Dockerfile`) |
| Baseline (upstream) | https://github.com/indico/indico, tag `v3.3.14`, commit **`a42252ead3509f9b31db0691cc9af899ab18416e`**, MIT |
| Container recipe | https://github.com/indico/indico-containers @ `5ebc1f3520144fd642c07abe95ac89d1bf5ba7fd` |
| Services | indico-web (uWSGI), celery, celery-beat, postgres:15-bookworm, redis, nginx |
| URL | http://localhost:8081 (8080 is used by another local project) |

Local changes to the container recipe:
- `indico.conf`: `SECRET_KEY` set, `DEFAULT_TIMEZONE='UTC'`, `BASE_URL=http://localhost:8081`, `PLUGINS=set()`
- `.env` created (DB credentials, `NGINX_PORT=8081`). This file is gitignored.
- `SECRET_KEY` is read from `INDICO_SECRET_KEY` in `.env`, so no secret is committed. See `.env.example`.
- `indico/modules/rb` is **bind-mounted from this repo** over the PyPI copy. At baseline the two were checked
  identical (`diff -rq`: no differing files). A temporary edit to an error message appeared in the API response after
  `docker compose restart indico-web` and disappeared after reverting, which proves repo changes reach the running app.
- `worker/*.sh` converted from CRLF to LF, because Windows git checkout broke the container entrypoint
  (`exec docker_entrypoint.sh: no such file or directory`). Add `* text=auto eol=lf` for `*.sh` in `.gitattributes`.

## Commands

```bash
# start (first time builds the image, ~5-10 min)
cd infra/indico-containers/indico-prod && docker compose up -d --build
# full reset + seed (≈1 min): wipes postgres/redis/file volumes, recreates schema, seeds, writes tests/team/.env.test
bash tests/team/seed/reset.sh
# stop
cd infra/indico-containers/indico-prod && docker compose down        # add -v to also wipe data
```

Seed data (`tests/team/seed/seed_rb.py`):
- users `admin`, `user1` and `mgr1` (password `<username>-Pass123!`)
- location "SQE Campus" and room **R1**: reservable, public, **needs confirmation**, `booking_limit_days = 7`
- `mgr1` holds the room `moderate` permission
- personal API tokens with scope `full:everything` for user1 and mgr1

## API results (Bearer token, JSON)

| # | Check | Request | Expected | Observed |
|---|---|---|---|---|
| 1 | WF-A create (pre-book) | `POST /rooms/api/booking/create` user1 | pending | **200**, `is_pending: true` ✅ |
| 2 | BR1 start in past | create, start yesterday | rejected | **418** "You cannot create a booking which starts in the past" ✅ |
| 3 | Schema: end ≤ start | create, end before start | rejected | **422** `webargs_errors._schema` "Booking cannot end before it starts" ✅ |
| 4 | FR-A5 direct book without right | create, `is_prebooking:false` user1 | denied | **403** "Not authorized to book this room" ✅ |
| 5 | FR-B5 non-moderator approves | `POST /bookings/1/approve` user1 | denied | **403** ✅ |
| 6 | WF-B approve | approve #1 mgr1 | accepted | **200**, `is_accepted: true` ✅ |
| 7 | BR3 approve accepted | approve #1 again | refused | **418** "already been approved or rejected" ✅ |
| 8 | Read back shared record | `GET /bookings/1` | accepted | **200**, `is_accepted: true` ✅ |
| 9 | Cross-workflow | user1 pre-books the now-accepted slot | refused | **418** "Reservation has no valid occurrences" ✅ |
| 10 | Reject without reason | `POST /bookings/3/reject {}` | 422 | **422** `reason: Missing data for required field` ✅ |
| 11 | WF-B reject | reject #3 with reason | rejected | **200**, `is_rejected: true` ✅ |
| 12 | BR3 approve rejected | approve #3 | refused | **418** ✅ |
| 13 | BR1 BVA (limit 7, daily repeat) | end − start = 6 / 7 / 8 days | allow / allow / reject | **200 / 200 / 418** ✅ |
| 14 | Reset | `GET /bookings/1` after `reset.sh` | gone | **404** ✅ |

## Findings to log as GitHub Issues / endpoint weaknesses (to triage)

1. **BR1 off-by-one interpretation.** With `booking_limit_days = 7`, an 8-calendar-day booking is accepted
   (`_validate_room_booking_limit` compares `(end_date 23:59 − start_date 00:00).days ≤ limit`). Decide from the docs
   whether this is a defect or intended, and document the decision.
2. **Rule rejections return HTTP 418 ("I'm a teapot")** with `{"message": ...}`, while schema errors return 422 with
   `webargs_errors` and access errors return 403 with `{"error": {...}}`. That gives three different error shapes for one API.
3. **Unknown booking id returns an HTML 404 page**, not JSON, on a `/rooms/api/` route.
4. **The overlap rejection message is vague**: "Reservation has no valid occurrences" does not tell the user the slot is already booked.

## Conclusion

Both workflows run fully through JSON HTTP endpoints, with token auth that needs no browser or CSRF token.
The four business rules and both roles behave as described in `docs/team/01-scope-draft.md`. The app installs, seeds and
fully resets locally in about 1 minute. **Indico Room Booking is feasible: register it.**
