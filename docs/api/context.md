# Area 2 project context

## System and repository

- **MIS:** Indico, CERN's open-source event and room-booking management system; the project scopes the Room Booking module (`indico/modules/rb`).
- **Upstream URL:** https://github.com/indico/indico
- **Team repository remote:** https://github.com/WrittenByAli/SE3002-SQE-Final-Project-.git
- **Licence:** MIT (`LICENSE`).
- **Exact local repository commit at the start of Fahima's work (`git rev-parse HEAD`):** `1cfc6db07b4d61a6ee0361ccd66b78f9dde563a3`.
- **Upstream Indico source baseline recorded in the repository README:** release `v3.3.14`, commit `a42252ead3509f9b31db0691cc9af899ab18416e`. This is distinct from the current team-repository HEAD above.

The local tree was clean on branch `main` when inspected. The team README describes the upstream source as imported at the pinned baseline; no source files were changed for this context note.

## Selected workflows and shared record

1. **Workflow A — request a room:** a regular user submits a future booking request for a reservable room configured to require confirmation. The expected result is a pending reservation.
2. **Workflow B — moderate the request:** a room moderator reviews that reservation and approves or rejects it; a pending request may also be cancelled by its booker. Approval makes the slot occupied, while rejection releases it.

**Shared record:** the `Reservation` (including its state and occurrences) and the room's availability for the same time slot. Workflow A creates the reservation and checks availability; Workflow B changes its state, which affects later availability and collision checks.

## Business rules in the current test basis

These are the four rules described in `docs/team/01-scope-draft.md`. That file labels its scope as a draft and says runtime confirmation is needed; they are test-basis statements, not results verified in this session.

| ID | Rule |
|---|---|
| BR1 | The booking start must not be in the past, and the booking length must be within the room's `booking_limit_days` (or the global limit when no room limit is set). |
| BR2 | A moderator may approve only a pending reservation. Both the pending state and moderator permission must hold. |
| BR3 | State changes are guarded: pending bookings may be accepted, rejected, or cancelled; accepted bookings may be cancelled under the documented permission/time conditions or rejected by a moderator; rejected and cancelled bookings are terminal. Confirm exact transitions against the running app before final reporting. |
| BR4 | Direct booking depends on room reservability and the applicable public/confirmation or explicit-book-right conditions. Otherwise, pre-booking is possible only when the user and room permit it. |

## Roles

- **Booker / regular user (`user1` in the synthetic seed):** can submit a permitted booking or pre-booking and cancel their own eligible booking; cannot moderate the room.
- **Room moderator (`mgr1` in the synthetic seed):** has room-level moderation rights and can approve or reject eligible reservations. A plain user must not receive those actions.

The account names and permissions above come from the team seed and scope documents. They are synthetic test identities, not observed API results from this session.

## Technology stack

- **Backend language/framework:** Python and Flask (Indico's package pins Python `~=3.12.2`).
- **Persistence:** PostgreSQL, accessed through SQLAlchemy.
- **Supporting services:** Redis and Celery.
- **Browser client:** React / JavaScript.
- **Local environment:** Docker Compose; the API checks use Python, pytest, and Requests according to the team setup files.

## Scope alignment items for the team

- The Area 2 task file names `tests/team/generator/` and `docs/team/api-testing.md` / `docs/team/data-generation.md`; Fahima's current authorized locations are `tools/testgen/`, `openapi/`, and `docs/api/`. Use the latter paths for her deliverables and record the path decision in the team plan.
- The assignment requires two Playwright use cases per member. Fahima's task file assigns UC-F1 and UC-F2 under `tests/team/e2e/`, which is outside her currently authorized write scope (`tests/team/api/` only). A teammate needs to own those artifacts or the allowed scope must be updated.
- Fahima is listed as lead for shared traceability, defect management/RCA, and weekly GQM reporting, normally under `docs/team/`. Those locations are outside her current authorized write scope. The team should assign an owner/location for these rubric items.
- The repository harness expects the shared AI-use row in `docs/team/ai-use-record.md` and prompts in `docs/team/ai-prompts/`; this request instead requires Fahima's log and prompts in `docs/ai-use/`. Keep the requested Fahima-specific record, and clarify with the team whether the shared record also needs a link or an owner update.
- The Area 2 checklist emphasizes body fields for create and approve/reject. The assignment says EP/BVA applies to every API input; clarify coverage of route parameters such as booking IDs and room IDs, plus the GET booking and timeline endpoints.
- A test-plan template exists, but `docs/team/test-plan.md` was absent at inspection. The plan, estimation, risk register, and exit criteria are shared/other-lead items that still need owners and completed evidence.
