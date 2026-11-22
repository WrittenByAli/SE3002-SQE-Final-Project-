# Section 1: System and Test Scope (DRAFT)

> Status: scope remains a draft. The upstream v3.3.14 baseline is frozen, and local setup/API checks are recorded in
> `docs/team/02-local-setup-verification.md`. Area 1 unit coverage and SonarQube metrics have not yet been measured.
> Review the proposed rule surface with the team before treating its coverage denominator as final.

---

## 1. Repository choice

**Indico** (https://github.com/indico/indico): an event and **room-booking management system** built by CERN
and used by many institutions.

| Item | Value |
|---|---|
| Stack | Python 3 / Flask, SQLAlchemy, PostgreSQL, Celery/Redis; React frontend |
| Licence | MIT |
| Activity (checked 2026-11-21) | ~2.1k stars, pushed 2026-11-20, not archived |
| Baseline (pinned) | tag **`v3.3.14`**, commit **`a42252ead3509f9b31db0691cc9af899ab18416e`**. This is the version running locally; see `docs/team/02-local-setup-verification.md` |
| Browser UI | Yes: `/rooms/` (React room-booking app) |
| HTTP API | Yes: JSON endpoints under `/rooms/api/...` (`indico/modules/rb/blueprint.py`) |
| Persistent storage | PostgreSQL |
| Test tools | pytest + coverage.py, mutmut, Playwright, k6 |

**Uniqueness check:** Indico does not appear on the Section A, B or C sheets (checked against the pasted lists).
pretix and pretalx are taken, but they are different projects from different developers.

**Known cost:** Indico is large and setup is heavier than for a toy app (PostgreSQL + Redis + a frontend build).
Try the install on day 1, before registering if possible. Keep the "all server-side business logic" coverage
target scoped to the room-booking (`rb`) logic you test, and justify that scope in the test plan.

---

## 1b. Selection checklist (source review, 2026-11-21; re-verify on local install)

| Requirement | Indico Room Booking | Status |
|---|---|---|
| HTTP API for both workflows | JSON endpoints for create, approve, reject and cancel (§1a); Bearer-token auth skips CSRF | ✅ in source; prove with curl |
| Not simple CRUD: 4 rules incl. boundary, ≥2-condition decision, state change | booking-limit + start-grace checks; `can_accept` user/pending/moderator guards; `Room.can_book`/`can_prebook` permissions; pending/accepted/rejected/cancelled transitions with guards | ✅ |
| Data dependency between workflows | A creates the `Reservation` (pending) and reads slot conflicts; B changes its state, which changes slot availability / prebooking collisions | ✅ |
| Local run, seed, reset | Needs PostgreSQL + Redis (+ Node for the UI build). Upstream ships pytest DB fixtures (`indico/testing/fixtures/database.py`, `database_docker.py`) and room/reservation factories (`rb.py`); reset = drop/recreate DB + `indico db prepare` + seed | ⚠️ heaviest risk; do the install first |
| CI feasible | Upstream `ci.yml` already runs pytest on `ubuntu-22.04` with a `postgres:14` service + apt redis. Reuse that pattern | ✅ |
| Toolchain | Python, so pytest + coverage.py, mutmut, SonarQube Python, Playwright, k6 | ✅ |
| Two roles with different permissions | regular user (pre-book only) vs room manager/moderator (approve/reject); `Forbidden` raised otherwise | ✅ |
| Raw backend source | Full source, MIT | ✅ |

**Scoping decisions to write in the test plan:**
- Proposed unit/coverage surface = the functions in `tests/team/rule_surface.yml`: booking-start grace and limit validation; booking creation authorization/processing; reservation creation and approval/rejection/cancellation rules; moderator action guards; and room book/pre-book permissions. Wania should review the list with Fahima and Ali before freezing it. Everything outside the selected two workflows needs an explicit scope justification.
- Run mutmut on those files only. A mutation run over the whole of Indico would be far too slow for CI.

**Business-rule labels:** BR1–BR4 are project IDs for traceability, not names built into Indico. These definitions are based on the pinned v3.3.14 source and still require confirmation against the running app before the scope is frozen.

---

## 1a. HTTP API check for the two workflows (source review, 2026-11-21)

Both workflows go through JSON endpoints, not server-rendered HTML forms. The React room-booking UI calls
these same endpoints, so API tests and Playwright tests exercise the same server logic.

| Workflow | Method + route | Input | Output | Handler |
|---|---|---|---|---|
| A: create booking | `POST /rooms/api/booking/create` | JSON body validated by `CreateBookingSchema` (webargs/marshmallow) | JSON `{room_id, booking, calendar_data}` | `RHCreateBooking` (`rb/controllers/backend/bookings.py`) |
| B: approve | `POST /rooms/api/bookings/<id>/approve` | JSON `{reason?: str, force?: bool}` | JSON `{booking}` | `RHBookingStateActions.accept` |
| B: reject | `POST /rooms/api/bookings/<id>/reject` | JSON `{reason: str}` (required) | JSON `{booking}` | `RHBookingStateActions.reject` |
| B: cancel | `POST /rooms/api/bookings/<id>/cancel` | none | JSON `{booking}` | `RHBookingStateActions` |
| Read back | `GET /rooms/api/bookings/<id>` and `GET /rooms/api/rooms/<room_id>/timeline` | none | JSON | `RHBookingDetails`, `RHTimeline` |

**Inputs for EP/BVA (`CreateBookingSchema`):**
- `start_dt`, `end_dt` (datetime, required; `start_dt < end_dt`, i.e. `start_dt >= end_dt` is rejected)
- `repeat_frequency` (enum, required; use `NEVER`)
- `repeat_interval` (int ≥ 0)
- `room_id` (int, required)
- `reason` (string; required depending on the `booking_reason_required` setting)
- `is_prebooking` (bool)
- `user` (principal)
- `admin_override_enabled` (bool)

The server-side rules then add the past-start check and the `booking_limit_days` limit.

**Authentication from pytest/k6 (no browser):** create a **personal API token** with scope `full:everything`
(user profile → API tokens) for `user1` and `mgr1`. Send it as `Authorization: Bearer <token>`.
`indico/web/util.py::_lookup_request_user` accepts it on every RH, and `indico/web/rh.py::_check_csrf` skips
the CSRF check for OAuth/token requests. The fallback is session cookie + `X-CSRF-Token` header.

**Caveats:**
- These are **internal JSON endpoints** used by Indico's own frontend, not a documented public REST API, and
  there is no OpenAPI file for them. The assignment allows this ("write an OpenAPI spec for your endpoints"),
  so the team writes `openapi/rb.yaml` from `CreateBookingSchema` and the handlers above.
- Rule rejections are raised as `ExpectedError`. **Check which HTTP status and JSON shape they return** on
  your install, and record any inconsistency as an "endpoint weakness".
- First practical test: send one create request and one approve request with `curl` and a Bearer token, before
  registering the repo.

---

## 2. Module and workflows

**Module:** Room Booking (`indico/modules/rb`)

| | Workflow A: Create a booking request (User) | Workflow B: Moderate the booking (Room manager) |
|---|---|---|
| Starting condition | Room "R1" is reservable, **requires confirmation** (`reservations_need_confirmation = True`), `booking_limit_days = 7`. User U1 can pre-book it. No bookings exist in the slot. | U1's booking for R1 is in state **pending**. M1 is a manager/moderator of R1. |
| User action | U1 books R1 for a future slot | M1 **approves** it (alternatives: rejects it with a reason; U1 cancels it) |
| Expected outcome | Reservation created with `state = pending` (pre-booking); shown in "My bookings" | Approve: `state = accepted` and the slot shows as booked on the timeline. Reject: `state = rejected` and the slot is free again |

**Shared record:** the `Reservation` (state + occurrences) for room R1, plus R1's **availability for that slot**.
- A **creates** the reservation and **reads** availability (conflicts).
- B **changes** the reservation state, which changes availability.
- Cross-workflow check: after B approves, a new A request for the same slot must conflict. After B rejects, it must not.

---

## 3. Functional requirements

| ID | WF | Requirement | Source |
|---|---|---|---|
| FR-A1 | A | A user can create a booking via the UI and `POST /rooms/api/booking/create`. | `rb/blueprint.py`, `RHCreateBooking` |
| FR-A2 | A | A booking that starts in the past is rejected ("You cannot create a booking which starts in the past"). | `controllers/backend/bookings.py` |
| FR-A3 | A | A booking period longer than the room's `booking_limit_days` (or the global `booking_limit`) is rejected. | `_validate_room_booking_limit` |
| FR-A4 | A | For a room that requires confirmation, a new booking is created as **pending**. Otherwise it is **accepted**. | `Reservation.create_from_data` (`prebook`) |
| FR-A5 | A | A user who may not book or pre-book the room gets 403 Forbidden. | `RHCreateBooking` / `Room.can_book`, `can_prebook` |
| FR-B1 | B | A room moderator can approve a pending booking (`POST /rooms/api/bookings/<id>/approve`). State becomes accepted. | `RHBookingStateActions`, `Reservation.accept` |
| FR-B2 | B | A moderator can reject a booking with a reason (`.../reject`). State becomes rejected. | `Reservation.reject` |
| FR-B3 | B | Approving a booking that is not pending is refused ("already been approved or rejected"). | `bookings.py` L267 |
| FR-B4 | B | Approving a pre-booking that collides with an accepted booking is refused (`prebooking_collision`) unless forced. | `RHBookingStateActions.accept` |
| FR-B5 | B | A user who is not a moderator cannot approve or reject (403). | `can_accept` / `can_reject` |

---

## 4. Business rules

| ID | Rule | Kind | Technique |
|---|---|---|---|
| **BR1** | A booking start must pass `is_booking_start_within_grace_period` (past starts are rejected unless the applicable admin override permits them). Its selected calendar-day period must be **≤** the room's `booking_limit_days`, or the global `booking_limit` when no room limit is set. The handler computes this period from start-date midnight to end-date 23:59. | **Boundary / limit** | Three-point BVA on the handler's computed period (limit−1 / limit / limit+1); derive start/end dates from that calculation. Separately test start-grace boundaries and the applicable override case. |
| **BR2** | `Reservation.can_accept(user)` returns true only when `user` is not `None`, the reservation is pending, and `room.can_moderate(user)` is true (subject to the function's `allow_admin` setting). | **Permission decision** | Unit/API cases for user presence, pending state, and moderator authorization; include denied combinations |
| **BR3** | State-action guards govern transitions: approval requires a pending reservation and `can_accept`; rejection is refused for rejected/cancelled reservations and requires `can_reject`; cancellation is refused for rejected/cancelled/archived reservations, and a non-pending reservation also needs an occurrence in the cancellation grace period. Cancellation then requires the owner/booked-for user or an allowed RB admin. Reservation states are pending, accepted, cancelled, and rejected. | **State transition + guarded decision** | In the selected create/moderate workflows, test pending→accepted/rejected/cancelled and accepted→rejected/cancelled, plus disallowed actions from each state. Include ownership/admin and grace-period conditions for cancellation. The accepted→pending reset triggered by editing a booking is outside the selected workflows and must be recorded as an explicit scope exclusion. |
| **BR4** | `Room.can_book` and `Room.can_prebook` require a user and a reservable room, except for the applicable room-admin bypass. Direct booking is allowed for public rooms that do not require confirmation, or users with book permission at the room/location. Pre-booking is allowed for public rooms that require confirmation, or users with the applicable pre-book permission. | **Permission decision** | Decision tables for both functions, covering public/confirmation settings, room reservability, permissions, user presence, and admin behavior |

> Source review in v3.3.14 (`rb/models/reservations.py`): `can_reject` blocks rejected/cancelled reservations. `can_cancel` also blocks archived reservations; accepted reservations need an occurrence in the cancellation grace period, and the caller must be the owner/booked-for user or an allowed RB admin (not an ordinary room moderator). Confirm these behaviors on the running app before finalising BR3; log a discrepancy as a defect.

---

### Business rules across test types

BR1–BR4 are shared requirements, not exclusive assignments. Members own testing techniques and apply them to every relevant rule in the frozen baseline:

| Rule | Unit / white-box (Wania) | API / generated data (Fahima) | Browser / quality checks (Ali) |
|---|---|---|---|
| BR1 booking start and limit | Boundary and rule-function unit cases | Generated EP/BVA request cases | Rejected-input/corrected-booking flow; usability/accessibility on the booking screen |
| BR2 approval eligibility | Decision cases for pending state and moderator permission | API role/state decisions and status/read-back | Moderator approval flow; access decision and usability/accessibility checks |
| BR3 guarded transitions and cancellation | State/guard unit cases; MCC/MC/DC target `Reservation.can_cancel` | Approve/reject/cancel API transitions, invalid transitions, repeats, and read-back | Browser approve/reject/cancel actions and role checks |
| BR4 direct-book / pre-book permissions | Unit cases for room settings, permissions, and admin behavior | Generated permission/API cases | User/manager access matrix and browser permission checks |

Performance/recovery applies to the operation the team selects (Area 3, Ali); it is not a separate exclusive BR assignment. All three members contribute to test management and traceability.

## 5. User roles

| Role | Account | Can | Cannot |
|---|---|---|---|
| Regular user (booker) | `user1` | search rooms, pre-book R1, view and cancel own bookings | approve or reject; book R1 directly (it needs confirmation) |
| Room manager / moderator | `mgr1` (manager of R1) | approve and reject any R1 booking | cancel other people's bookings (`can_cancel` = booker or RB admin only); moderate rooms they don't manage (**verify**) |
| (Admin, setup only) | `admin` | create location and rooms, set limits | not a tested role |

---

## 6. Test basis and assumptions

- Basis: source code (`indico/modules/rb/**`), Indico docs (https://docs.getindico.io), and the running UI.
- **A-1:** Single (non-repeating) bookings only. Recurring bookings are out of scope.
- **A-2:** Room R1 `booking_limit_days = 7`, `max_advance_days` unset. The global `booking_limit` is left at default.
- **A-3:** Email notifications are disabled or captured locally and are not asserted.
- **A-4:** Fixed timezone (UTC) in the test environment, to avoid date-boundary flakiness.

---

## 7. Commands (verified 2026-11-21, see `docs/team/02-local-setup-verification.md`)

```bash
# Run the app (Docker: Indico 3.3.14 + PostgreSQL + Redis + nginx) on http://localhost:8081
cd infra/indico-containers/indico-prod && docker compose up -d --build
# Full reset + seed (wipes volumes, recreates schema, seeds users/room/tokens, writes tests/team/.env.test)
bash tests/team/seed/reset.sh
```

For white-box unit tests and mutation, you also need the **source** at the baseline commit:
`git clone https://github.com/indico/indico.git && git checkout v3.3.14` (commit `a42252e…`). Use its pytest
fixtures (`indico/testing/fixtures/`), which need a PostgreSQL test DB.

Team tests live in `tests/team/` (unit/, api/, e2e/, perf/, generator/). Upstream tests earn no marks.
