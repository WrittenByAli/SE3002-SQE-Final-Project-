# UC-A1: User submits a booking with a rule violation, then corrects it

| Field | Value |
|---|---|
| Author (writes + automates it) | Muhammad Ali (`WrittenByAli`) |
| Actor(s) | `user1` (authenticated booker) |
| Traces to | FR-A2 (past start rejected), FR-A3 (booking limit rejected), FR-A4 (confirmed room → pending), BR1 (boundary: start not in past, length ≤ booking_limit_days) |
| Preconditions | (1) App running at http://localhost:8081. (2) `user1` is logged in. (3) Room R1 exists, `reservations_need_confirmation = True`, `booking_limit_days = 7`. (4) The target slot is free (no conflicting bookings). |
| Postconditions (checkable) | A `Reservation` record exists in the DB with `state = pending`, linked to `user1` and R1 for the corrected slot. The booking appears under "My bookings" in the UI. The room timeline shows the slot as tentatively occupied. |
| Playwright test file | `tests/team/e2e/tests/uc-a1-rule-violation-correction.spec.ts` |

## Main flow

1. `user1` navigates to http://localhost:8081/rooms/ and clicks **Book a room**.
2. System displays the room search / booking form.
3. `user1` selects Room R1, sets **start date to yesterday** (past), sets end date to today, sets reason, and clicks **Book**.
4. System rejects the submission and displays the error: *"You cannot create a booking which starts in the past"*.
5. `user1` corrects the start date to **tomorrow** and sets end date to **the day after tomorrow** (2-day span, within the 7-day limit), keeping the reason, and clicks **Book**.
6. System accepts the submission and displays a confirmation: booking created as **pending** (awaiting moderator approval).
7. `user1` navigates to **My bookings**.
8. System shows the new booking with status **Pending**.

## Alternative flows

- **A1** (from step 3): `user1` sets the booking span to **8 days** (exceeds `booking_limit_days = 7`).
  System rejects with an error about the booking limit. `user1` reduces the span to 6 days. System accepts; booking is created as pending. → Verifies BR1 upper boundary.

- **A2** (from step 3): `user1` sets end date before start date (`end_dt < start_dt`).
  System rejects with a schema-level error (*"Booking cannot end before it starts"*). `user1` swaps the dates. System accepts the corrected booking as pending.

## Exception flows

- **E1** (from step 3): `user1` submits with the **reason field empty** and the room requires a reason (`booking_reason_required = True`).
  System returns a 422 validation error listing "reason: Missing data for required field". `user1` does not complete the booking; the slot remains free.

- **E2** (from step 2): `user1` is **not authorised to book or pre-book** R1 (permission revoked between login and submission).
  System returns 403 *"Not authorized to book this room"*. The booking is not created; `user1` is shown an access-denied message.

## Automation map

| Flow | test() title | Asserts shown result | Asserts postcondition (how) |
|---|---|---|---|
| Main (past start → corrected) | `BR1 EP past-start rejected then corrected booking created as pending` | Error message text visible after first submit; confirmation visible after second submit | `GET /rooms/api/bookings/<id>` → `is_pending: true`; booking appears in My-bookings UI |
| A1 (8-day span → corrected) | `BR1 BVA 8-day span rejected then 6-day accepted as pending` | Booking-limit error visible; confirmation visible after correction | `GET /rooms/api/bookings/<id>` → `is_pending: true` |
| A2 (end before start → corrected) | `BR1 schema end-before-start rejected then corrected` | Schema error visible; confirmation visible | `GET /rooms/api/bookings/<id>` → `is_pending: true` |
| E1 (empty reason) | `FR-A3 missing reason field returns validation error` | Validation error visible; no confirmation | `GET /rooms/api/bookings` list unchanged (no new booking for user1) |
| E2 (unauthorised) | `FR-A5 unauthorised user gets 403` | 403 / access-denied shown | No booking created (list unchanged) |
