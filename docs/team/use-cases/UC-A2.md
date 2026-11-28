# UC-A2: User views booking status and room timeline after a moderator decision (keyboard-only)

| Field | Value |
|---|---|
| Author (writes + automates it) | Muhammad Ali (`WrittenByAli`) |
| Actor(s) | `user1` (booker, keyboard-only navigation); `mgr1` (moderator, precondition setup via API) |
| Traces to | FR-B1 (approve → accepted), FR-B2 (reject → rejected), FR-B3 (double-approve refused), FR-B5 (non-moderator cannot approve), BR3 (state transitions: pending → accepted / rejected) |
| Preconditions | (1) App running at http://localhost:8081. (2) `user1` is logged in with keyboard-only navigation (no mouse). (3) A `Reservation` for R1 exists in state **pending**, booked by `user1`, created via `env-reset` + API seed or prior test step. (4) `mgr1` has already approved or rejected the booking (set up via API before the test, not through the UI in this UC). |
| Postconditions (checkable) | The UI reflects the booking's current state (accepted or rejected). The room timeline (`GET /rooms/api/rooms/<id>/timeline`) confirms the slot is booked (accepted) or free (rejected). `user1` reached every required UI element using keyboard only (Tab / Enter / Space). |
| Playwright test file | `tests/team/e2e/tests/uc-a2-booking-status-keyboard.spec.ts` |

## Main flow (booking approved; keyboard-only navigation)

1. `user1`'s pending booking for R1 has been **approved** by `mgr1` via the API (`POST /rooms/api/bookings/<id>/approve`) in the test setup step.
2. `user1` focuses the browser address bar (or the page already loads at `/rooms/`).
3. `user1` uses **Tab** to navigate to the **My bookings** link in the navigation bar and presses **Enter**.
4. System displays the list of `user1`'s bookings.
5. `user1` uses **Tab** to navigate to the booking row for R1 and presses **Enter** to open the detail view.
6. System displays the booking detail with status **Accepted** and the approved dates.
7. `user1` uses **Tab** to navigate to the **Room timeline** link and presses **Enter**.
8. System displays the room timeline for R1 showing the slot as **booked** (the accepted reservation appears in the calendar grid).
9. `user1` confirms: status = Accepted, slot is occupied on the timeline.

## Alternative flows

- **A1** (from step 1): The booking was **rejected** by `mgr1` instead (`POST /rooms/api/bookings/<id>/reject` with a reason).
  After step 6, the status shows **Rejected** with the rejection reason. After step 8, the timeline shows the slot as **free**. → Verifies BR3 pending → rejected.

- **A2** (from step 1): The booking is still **pending** (no moderator action taken yet).
  Step 6 shows status **Pending**. The timeline shows the slot as tentatively occupied (pending). `user1` can still cancel from the detail view using keyboard navigation.

## Exception flows

- **E1** (from step 3): The **My bookings** navigation link is not reachable by Tab before timing out (focus trap or missing tabindex).
  Test fails the focus-order assertion. Logged as an accessibility defect. The booking status is not checked.

- **E2** (from step 5): The booking row in the list is not keyboard-activatable (missing `role="button"` or `tabindex`).
  Test fails the keyboard assertion. Logged as an accessibility defect. The booking detail is not reached.

## Automation map

| Flow | test() title | Asserts shown result | Asserts postcondition (how) |
|---|---|---|---|
| Main (approved, keyboard) | `BR3 pending→accepted: user1 views accepted booking status via keyboard` | Status badge text = "Accepted"; timeline slot occupied | `GET /rooms/api/bookings/<id>` → `is_accepted: true`; `GET /rooms/api/rooms/<id>/timeline` → slot present |
| A1 (rejected, keyboard) | `BR3 pending→rejected: user1 views rejected booking status via keyboard` | Status badge text = "Rejected" + reason shown; timeline slot free | `GET /rooms/api/bookings/<id>` → `is_rejected: true`; timeline → slot absent |
| A2 (still pending) | `BR3 pending state: user1 views pending booking via keyboard` | Status badge text = "Pending" | `GET /rooms/api/bookings/<id>` → `is_pending: true` |
| E1 (focus not reachable) | `A11y: My-bookings link reachable by Tab from page load` | Focus reaches nav link within 15 Tab presses | — (accessibility assertion) |
| E2 (row not activatable) | `A11y: booking row activatable by Enter key` | Booking detail opens on Enter | — (accessibility assertion) |
