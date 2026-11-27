# Room Booking API inventory

Inventory for the two workflows in [context.md](context.md): a booker requests a room, then a room moderator approves or rejects that request; the booker may cancel an eligible request. The shared record is the reservation and its occurrences, which affect room availability.

## Runtime and authentication

Live requests were run against the local Indico `v3.3.14` stack on 2026-11-27 using the seeded `user1` and `mgr1` personal tokens. Token values are not stored in this document or the evidence files. Rejection requests included `X-Requested-With: XMLHttpRequest`, matching Indico's browser client and yielding the JSON error shape. JSON request bodies were supplied as UTF-8 without a byte-order mark.

All routes below are under the `/rooms` blueprint (`indico/modules/rb/blueprint.py:19-20`). Handlers inherit `RHRoomBookingBase`: the caller must be authenticated and have Room Booking access (`indico/modules/rb/controllers/__init__.py:17-25`; `indico/web/rh.py:371-379`; `indico/modules/rb/util.py:46-56`). Anonymous timeline access returned 403 ([curl](evidence/room-timeline-anonymous.txt)). The OAuth bearer scope is `read:everything` or `full:everything` for GET and `full:everything` for non-GET (`indico/web/util.py:309-349`; OAuth requests bypass CSRF checks in `indico/web/rh.py:220-233`).

`user1` is the seeded regular booker; `mgr1` has room-level `moderate` permission. Source permission rules are in `indico/modules/rb/models/rooms.py:621-660` and the seed setup is in `tests/team/seed/seed_rb.py`. Live calls confirmed that `user1` can prebook and cancel their own pending request, cannot directly book this confirmation-required room, and cannot approve it; `mgr1` can approve and reject it.

The schemas declare Marshmallow `DateTime` fields. The working local format observed here is a naive local timestamp such as `2026-11-30T10:00:00`. A `Z` timezone suffix was accepted by parsing but led to a 500 during serialization; see the runtime findings. The evidence files contain the actual curl status line, response headers, and body for each linked request.

## 1. Read one room's timeline

**GET `/rooms/api/rooms/<int:room_id>/timeline`** — route `indico/modules/rb/blueprint.py:51`; request and response handling `indico/modules/rb/controllers/backend/bookings.py:58-94`.

| Request field | Type and format | Required/default | Limits and rule | Source |
|---|---|---|---|---|
| `room_id` (path) | Integer path segment | Required | Must identify a non-deleted room. No additional numeric bound is declared in this handler. | `bookings.py:59-62` |
| `start_dt` | Date-time string | Required | No schema min/max. Defines the start of the requested availability range. Use naive local ISO form in this running version. | `bookings.py:64-66`; runtime evidence below |
| `end_dt` | Date-time string | Required | No schema min/max. Defines the end of the requested range. | `bookings.py:64-66` |
| `repeat_frequency` | Enum string: `NEVER`, `DAY`, `WEEK`, `MONTH` | Optional; source default `NEVER` | Supplying `NEVER` explicitly succeeds. Omitting it currently reaches a 500; do not treat the declared default as working. | `bookings.py:67`; enum `indico/modules/rb/models/reservations.py:44-49`; recurrence `indico/modules/rb/models/reservation_occurrences.py:201-230` |
| `repeat_interval` | Integer | Optional; default `1` | No field min/max here. Recurrence generation requires `DAY=1`, `WEEK>0`, and `MONTH!=0`; ignored for `NEVER`. | `bookings.py:68`; `reservation_occurrences.py:207-222` |
| `recurrence_weekdays` | Array of strings | Optional; default `null` | Each value must be one of `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`. No list-length or duplicate check in this query schema; used for weekly recurrence. | `bookings.py:69`; `indico/modules/rb/util.py:39` |
| `skip_conflicts_with` | Array of integers | Optional; default `null` | No explicit range or array-length limit. Identifies bookings excluded from conflict checks. | `bookings.py:70`; availability operations `indico/modules/rb/operations/bookings.py:103-155` |
| `admin_override_enabled` | Boolean | Optional; default `false` | Enables applicable administrator override checks; regular user is not entitled to use administrator privileges. | `bookings.py:71`; room permissions `indico/modules/rb/models/rooms.py:648-660` |

**Shared records:** reads the room, reservation occurrences, pending/accepted reservations, room blockings, non-bookable periods, and bookable hours; it does not mutate the reservation. Availability computation and serialization are in `indico/modules/rb/operations/bookings.py:103-155` and `indico/modules/rb/util.py:253-260`.

**Response:** HTTP 200 returns `{ "availability": <room availability object>, "date_range": ["YYYY-MM-DD", ...] }`. The availability object includes candidates, bookings/pre-bookings, conflicts, rejections/cancellations, blockings, non-bookable periods, and counts. Explicit `NEVER` with naive dates returned 200 ([curl](evidence/room-timeline-user1-naive.txt)).

## 2. Read availability for multiple rooms

**POST `/rooms/api/timeline`** — route `indico/modules/rb/blueprint.py:64`; UI calls this for room selection/timeline availability (`indico/modules/rb/client/js/modules/bookRoom/actions.js:132-179`).

The query fields are the same as the room timeline above (`start_dt`, `end_dt`, `repeat_frequency`, `repeat_interval`, `recurrence_weekdays`, `skip_conflicts_with`, and `admin_override_enabled`) and are parsed from the query string (`bookings.py:64-74`). The JSON body field is:

| Request field | Type | Required/default | Limits and rule | Source |
|---|---|---|---|---|
| `room_ids` (body) | Array of integers | Optional; default `[]` | No explicit minimum, maximum, or length. Selects the active rooms to include; response order follows the supplied ID order. | `bookings.py:73-94` |

**Shared records:** reads availability and the same reservations/occurrences and room restrictions as GET timeline. No records are changed (`indico/modules/rb/operations/bookings.py:103-155`).

**Response:** HTTP 200 returns `{ "availability": [[room_id, availability_object], ...], "date_range": [...] }`. This runtime shape is a list of room-ID/availability pairs for the multi-room route; the one-room route returns the room availability object directly. A successful request is captured in [curl evidence](evidence/multiroom-timeline-user1.txt). Sending no query dates returned 422 with missing `start_dt` and `end_dt` errors ([curl evidence](evidence/multiroom-timeline-user1-body-all.txt)).

## 3. Create a room booking or prebooking

**POST `/rooms/api/booking/create`** — route `indico/modules/rb/blueprint.py:67`; controller `indico/modules/rb/controllers/backend/bookings.py:171-231`; schema `indico/modules/rb/schemas.py:407-456`.

| Request field | Type and format | Required/default | Limits and rule | Source |
|---|---|---|---|---|
| `start_dt` | Date-time string | Required | No length or numeric bounds. Must precede `end_dt`; a start in the past is rejected. Use naive local ISO form here. | `schemas.py:411,427-432`; `bookings.py:200-206`; `indico/modules/rb/util.py:188-202` |
| `end_dt` | Date-time string | Required | No length or numeric bounds. The room/global booking-length limit applies. `NEVER` recurrence must start and end on the same calendar date. | `schemas.py:412,427-432`; `bookings.py:208-213`; `indico/modules/rb/models/reservations.py:294-296` |
| `repeat_frequency` | Enum string: `NEVER`, `DAY`, `WEEK`, `MONTH` | Required | Controls occurrence generation. | `schemas.py:413`; enum `reservations.py:44-49`; recurrence `reservation_occurrences.py:201-230` |
| `repeat_interval` | Integer | Optional; default `0` | Minimum `0`; no declared maximum. Recurrence combinations have additional frequency-specific rules: `DAY` requires 1, `WEEK` must be positive, and `MONTH` must be nonzero. | `schemas.py:414`; `reservation_occurrences.py:207-222` |
| `recurrence_weekdays` | Array of strings | Optional | Values must be `mon` through `sun`; duplicates are rejected. It is retained only for weekly recurrence and cleared for other frequencies. No explicit list-length limit. | `schemas.py:415,433-436,450-456`; weekdays `rb/util.py:39` |
| `room_id` | Integer | Required | Must identify an existing, non-deleted room; the current user must be allowed to book or prebook according to `is_prebooking`. | `schemas.py:416`; `bookings.py:173-182` |
| `user` | Principal identifier string | Optional; omitted means authenticated user | Principal format is a typed identifier such as `User:<id>:<signature>`; external users are enabled on this field. No string length limit declared. | `schemas.py:417`; `indico/util/marshmallow.py:341-360`; parser `indico/util/user.py:34-83`; default `bookings.py:201` |
| `reason` | String | Optional at field level; default `""` | No `Length` validator or database length limit (`db.Text`). Current Room Booking setting requires a non-empty reason; empty/missing reason returned 422. | `schemas.py:418,438-449`; default setting `indico/modules/rb/__init__.py:47-71`; model `reservations.py:176-181` |
| `internal_note` | String | Optional | No declared length limit; persistence is conditional on internal-notes configuration/permission. | `schemas.py:419`; `reservations.py:189-195,306-310` |
| `is_prebooking` | Boolean | Optional; default `false` | `true` requests moderator confirmation and uses prebook permission; `false` requires direct-book permission. For seeded public room `R1`, confirmation is required, so `user1` can prebook but direct booking returned 403. | `schemas.py:420`; `bookings.py:173-182`; `rooms.py:621-660` |
| `link_type` | Enum string: `category`, `event`, `contribution`, `subcontribution`, `session`, `session_block` | Optional | Describes the linked Indico object. | `schemas.py:421`; `indico/core/db/sqlalchemy/links.py:22-38` |
| `link_id` | Integer | Optional | Object identifier; a link is processed when both type and ID are present. No explicit numeric bound declared. | `schemas.py:422`; `bookings.py:186-198` |
| `link_back` | Boolean | Optional; default `false` | Requests that a permitted link update the linked object's room association. | `schemas.py:423`; `bookings.py:186-198` |
| `admin_override_enabled` | Boolean | Optional; default `false` | Controls administrator override of applicable time/room checks. | `schemas.py:424`; `bookings.py:200-213` |
| `extra_fields` | Object/dictionary | Optional; default `{}` | No schema-level key, value, or size limit declared here. | `schemas.py:425` |

**Shared records:** creates a `Reservation`, associated occurrence records, edit/notification side effects, and an availability entry. With the seeded confirmation-required room, a permitted `is_prebooking=true` request creates a pending reservation (`indico/modules/rb/models/reservations.py:280-322`). The controller checks room access, start time, and duration (`bookings.py:178-218`).

**Response:** HTTP 200 returns `{ "room_id": id, "booking": booking_object, "calendar_data": { "pre_bookings"|"bookings": ... } }`. The successful JSON body showed booking ID 2 with `state: "pending"` ([curl evidence](evidence/create-prebooking-user1-json.txt)).

## 4. Read a booking

**GET `/rooms/api/bookings/<int:booking_id>`** — route `indico/modules/rb/blueprint.py:70`; handler `indico/modules/rb/controllers/backend/bookings.py:238-250`.

| Request field | Type | Required/default | Limits and rule | Source |
|---|---|---|---|---|
| `booking_id` (path) | Integer path segment | Required | Must identify an existing reservation whose room is not deleted; no additional numeric bound is declared. | `bookings.py:238-244` |

No body or query fields. The authenticated Room Booking user must be allowed to access the route; serialized detail may hide fields under the `hide_booking_details` setting (`indico/modules/rb/models/reservations.py:477-480`).

**Shared records:** reads the reservation, its occurrences/edit log, same-room bookings, room blockings, bookable hours, and non-bookable periods; no mutation (`indico/modules/rb/util.py:206-248`).

**Response:** HTTP 200 returns the booking details object directly (not wrapped in a `booking` key), including reservation fields, `state`, `date_range`, grouped `occurrences`, and permissions. Booking 2 readback returned the pending booking and grouped occurrence data ([curl evidence](evidence/booking-detail-user1.txt)). Unknown ID returned 404 with `{ "error": {"title", "message", "error_uuid"} }` ([curl evidence](evidence/booking-detail-missing-user1.txt)).

## 5. Approve, reject, or cancel a booking

**POST `/rooms/api/bookings/<int:booking_id>/<action>`**, where `<action>` is `approve`, `reject`, or `cancel` — route `indico/modules/rb/blueprint.py:75-76`; controller `indico/modules/rb/controllers/backend/bookings.py:240-300`.

| Request field | Type and format | Required/default | Limits and rule | Source |
|---|---|---|---|---|
| `booking_id` (path) | Integer path segment | Required | Must identify a reservation with a non-deleted room. | `bookings.py:240-244` |
| `action` (path) | Enum path segment: `approve`, `reject`, `cancel` | Required | Only these three action names are declared by the route; an unsupported `archive` request returned 405. | `blueprint.py:75-76`; [curl evidence](evidence/booking-action-invalid-405.txt) |
| `reason` for `approve` | String | Optional | No declared length limit. Included in the approval edit log if non-empty. | `bookings.py:281-291`; `reservations.py:386-394` |
| `force` for `approve` | Boolean | Optional; default `false` | If false, an approval checks prebooking collisions; true permits that collision check to be bypassed. | `bookings.py:281-291` |
| `reason` for `reject` | String | Required | The request schema declares no minimum length, but the reservation and occurrence tables have a non-empty database check. An empty value passed field parsing and returned 500 in the fresh probe; a non-empty value returned 200. | `bookings.py:275-279`; `reservations.py:422-433`; `reservations.py:105`; `reservation_occurrences.py:70`; [live probe](evidence/spec-vs-actual-live.txt) |
| Body for `cancel` | No fields used | Not required | Cancel is permitted to the owner/booked-for user or an RB admin. Pending requests may be cancelled; accepted requests require the cancellation grace period. Rejected/cancelled/archived bookings cannot be cancelled. | `bookings.py:293-300`; `reservations.py:404-420,451-461` |

**Role/state checks:** approval requires both pending state and moderator permission (`Reservation.can_accept`, `reservations.py:439-442`). Rejection requires moderator permission and excludes already rejected/cancelled reservations (`can_reject`, `reservations.py:444-449`). Cancellation uses ownership/admin and state/time checks (`can_cancel`, `reservations.py:451-461`). A regular user attempting approval returned 403. Repeated approve/reject/cancel transitions returned 418 `ExpectedError` JSON messages (`bookings.py:257-273`; `indico/web/flask/errors.py:40-44`; `indico/web/util.py:123-142`).

**Shared records:** all successful actions update reservation state and edit logs and update occurrence state/availability (`reservations.py:386-433`). Approve returns accepted state; reject returns rejected state and rejection reason; cancel returns cancelled state. HTTP 200 responses wrap detail as `{ "booking": booking_object }`.

## Observed runtime outcomes

The table reports only status codes actually observed in curl calls. The evidence files include the response body.

| Endpoint/check | Observed result | Evidence |
|---|---|---|
| Anonymous GET room timeline | 403 | [room-timeline-anonymous.txt](evidence/room-timeline-anonymous.txt) |
| GET room timeline with explicit `repeat_frequency=NEVER` and naive dates | 200; availability JSON | [room-timeline-user1-naive.txt](evidence/room-timeline-user1-naive.txt) |
| GET room timeline with `repeat_frequency` omitted | 500; `Unexpected frequency NEVER` | [room-timeline-default-frequency.txt](evidence/room-timeline-default-frequency.txt) |
| GET room timeline with ISO `Z` dates and explicit `NEVER` | 500; `AssertionError: expected naive datetime` | [room-timeline-timezone-aware.txt](evidence/room-timeline-timezone-aware.txt) |
| POST multi-room timeline with room ID and query dates | 200; availability list and date range | [multiroom-timeline-user1.txt](evidence/multiroom-timeline-user1.txt) |
| POST multi-room timeline without query dates | 422; required `start_dt` and `end_dt` errors | [multiroom-timeline-user1-body-all.txt](evidence/multiroom-timeline-user1-body-all.txt) |
| POST create valid prebooking (`user1`) | 200; booking 2 created pending | [create-prebooking-user1-json.txt](evidence/create-prebooking-user1-json.txt) |
| POST create with empty body | 422; required `start_dt`, `end_dt`, `repeat_frequency`, `room_id` | [create-missing-fields-user1.txt](evidence/create-missing-fields-user1.txt) |
| POST create without reason | 422; `Booking reason not specified` under `reason` | [create-missing-reason-user1.txt](evidence/create-missing-reason-user1.txt) |
| POST create with `repeat_interval=-1` | 422; `Invalid value` | [create-negative-interval-user1.txt](evidence/create-negative-interval-user1.txt) |
| POST direct booking by `user1` in confirmation-required room | 403; `Not authorized to book this room` | [create-direct-user1-forbidden.txt](evidence/create-direct-user1-forbidden.txt) |
| GET booking 2 | 200; detail object | [booking-detail-user1.txt](evidence/booking-detail-user1.txt) |
| GET unknown booking 999999 | 404 | [booking-detail-missing-user1.txt](evidence/booking-detail-missing-user1.txt) |
| POST approve by `user1` | 403 | [approve-user1-forbidden.txt](evidence/approve-user1-forbidden.txt) |
| POST approve by `mgr1` | 200; state accepted | [approve-mgr1.txt](evidence/approve-mgr1.txt) |
| Repeat approve on accepted booking | 418; already approved/rejected | [approve-already-approved-mgr1.txt](evidence/approve-already-approved-mgr1.txt) |
| POST reject without reason | 422; required `reason` | [reject-missing-reason-mgr1.txt](evidence/reject-missing-reason-mgr1.txt) |
| POST reject by `mgr1` with reason | 200; state rejected | [reject-mgr1.txt](evidence/reject-mgr1.txt) |
| Repeat reject on rejected booking | 418; already cancelled/rejected | [reject-already-rejected-mgr1.txt](evidence/reject-already-rejected-mgr1.txt) |
| POST cancel by owning `user1` | 200; state cancelled | [cancel-user1.txt](evidence/cancel-user1.txt) |
| Repeat cancel on cancelled booking | 418; already cancelled/rejected | [cancel-already-cancelled-user1.txt](evidence/cancel-already-cancelled-user1.txt) |
| POST unsupported action `archive` | 405 | [booking-action-invalid-405.txt](evidence/booking-action-invalid-405.txt) |

## Test basis: documented behavior, source behavior, and assumptions

The workflow rules BR1–BR4 in `context.md` come from the team's scope-draft document, which labels them as a draft, not from an external Indico API specification. Source code confirms the booking-time/length checks, role/state checks, and direct-book/prebook permission split. The live checks confirmed pending creation, moderator approval and rejection, user's inability to approve/direct-book, and cancellation by the booker.

**Suspected upstream defects (observed; source unchanged):**

- The timeline schema sets `repeat_frequency`'s default to the string `'NEVER'` (`bookings.py:67`), but recurrence code compares it to the enum and falls through to `Unexpected frequency NEVER` (`reservation_occurrences.py:201-230`). The endpoint returns 500 if this optional field is omitted. Supplying `NEVER` explicitly returns 200.
- `DateTime` parsing accepts timezone-aware ISO input, but timeline serialization expects naive datetimes and raises `AssertionError: expected naive datetime` (trace ends at `indico/util/marshmallow.py:140-145`). A naive local timestamp returned 200. This is a runtime constraint/bug, not a documented client guarantee.

**Assumptions to keep explicit in test basis:**

- The project draft expects rejection/cancellation to make the slot reusable. Action responses moved occurrences into rejected/cancelled groups, but this run did not issue a follow-up create for those exact slots; immediate rebooking remains unverified.
- Only `NEVER` recurrence was exercised successfully. Other frequency/interval combinations are source-derived rules, not live results from this run.
- Accepted-booking cancellation grace-period behavior was not exercised; only pending cancellation was.
- API status/body details here are runtime observations. The schema/source rules do not promise a specific HTTP status for every internal error.
