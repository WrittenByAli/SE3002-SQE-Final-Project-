# Reproducible API weaknesses

This list is based on live responses recorded in the 2026-11-27 API run. It separates observed application behavior from contract/test-basis assumptions. The likelihood and impact values use 1 (low) through 5 (high); risk score is likelihood × impact. The issue drafts below are ready to paste into GitHub Issues.

## 1. Timeline default recurrence returns HTTP 500

- **Endpoint:** `GET /rooms/api/rooms/{room_id}/timeline`; also observed on `POST /rooms/api/timeline`.
- **Reproduction:** Use a valid room and valid date range, but omit `repeat_frequency`. Example: `GET /rooms/api/rooms/1/timeline?start_dt=2026-11-30T10%3A00%3A00&end_dt=2026-11-30T11%3A00%3A00` with a valid read token.
- **Observed response:** `500 application/json`, `{"error":{"error_uuid":"7f461865-9997-4201-b2ad-b3c1e6cc9ac4","message":"Unexpected frequency NEVER","title":"Something went wrong"}}`. Captured in [room-timeline-default-frequency.txt](evidence/room-timeline-default-frequency.txt); generated cases API-0028 and API-0083 also observed 500 when omitting the optional field.
- **Expected:** The field is optional and its source default is `NEVER`; a valid single-date availability request should return 200.
- **Likely root cause:** The Marshmallow `fields.Enum` default is the string `'NEVER'`, while recurrence generation expects the `RepeatFrequency.NEVER` enum value. This is an inference from the observed exception and source path `indico/modules/rb/controllers/backend/bookings.py` and `indico/modules/rb/models/reservation_occurrences.py`.
- **Severity:** High (server error for a valid request). **Likelihood 4 × impact 4 = 16/25.**
- **Proposed fix:** Normalize the default through the enum (or use the enum member as the default); add API tests for omitted frequency on both timeline methods.

### GitHub Issue draft

**Title:** Timeline API returns 500 when optional `repeat_frequency` is omitted

**Steps to reproduce**

1. Authenticate with a Room Booking token that can read room 1.
2. Send `GET /rooms/api/rooms/1/timeline?start_dt=2026-11-30T10%3A00%3A00&end_dt=2026-11-30T11%3A00%3A00` without `repeat_frequency`.

**Expected:** HTTP 200 with availability for the requested range; the documented default is `NEVER`.

**Actual:** HTTP 500 JSON with title `Something went wrong` and message `Unexpected frequency NEVER`.

**Severity:** High. **Priority:** P1.

---

## 2. Offset-bearing RFC 3339 date-times cause HTTP 500

- **Endpoint:** `GET /rooms/api/rooms/{room_id}/timeline` (the same timeline implementation serves the multi-room route).
- **Reproduction:** Send otherwise valid RFC 3339 values with a timezone suffix, e.g. `GET /rooms/api/rooms/1/timeline?start_dt=2026-11-30T10%3A00%3A00Z&end_dt=2026-11-30T11%3A00%3A00Z&repeat_frequency=NEVER`.
- **Observed response:** `500 application/json`, `{"error":{"error_uuid":"c2d724fd-29f2-45bc-8aa5-e806da37a55d","message":"AssertionError: expected naive datetime","title":"Something went wrong"}}`. See [room-timeline-timezone-aware.txt](evidence/room-timeline-timezone-aware.txt) and the runtime comparison evidence.
- **Expected:** Accept RFC 3339 date-time values with an offset and consistently convert them to the application's timezone model, or reject unsupported offset values with a client error rather than a server error.
- **Likely root cause:** The OpenAPI contract declares `format: date-time` (RFC 3339), while downstream room-booking code asserts naive datetimes. The input contract and runtime timezone model disagree.
- **Severity:** High. **Likelihood 3 × impact 4 = 12/25.**
- **Proposed fix:** Choose and document a timezone policy; normalize aware inputs before availability calculations, or validate naive-only input explicitly and return 422. Align OpenAPI and tests with that policy.

### GitHub Issue draft

**Title:** Timeline API raises 500 for RFC 3339 date-times with timezone offsets

**Steps to reproduce**

1. Authenticate with a token that can read room 1.
2. Send `GET /rooms/api/rooms/1/timeline?start_dt=2026-11-30T10%3A00%3A00Z&end_dt=2026-11-30T11%3A00%3A00Z&repeat_frequency=NEVER`.

**Expected:** HTTP 200 after timezone normalization, or a clear 4xx validation response if offsets are unsupported.

**Actual:** HTTP 500 JSON with `AssertionError: expected naive datetime`.

**Severity:** High. **Priority:** P1.

---

## 3. Wrong JSON type for the booked-for principal causes HTTP 500

- **Endpoint:** `POST /rooms/api/booking/create`.
- **Reproduction:** Send an otherwise valid booking JSON body with `"user": 1`; for example `{"start_dt":"2036-01-06T09:00:00","end_dt":"2036-01-06T10:00:00","repeat_frequency":"NEVER","repeat_interval":0,"room_id":1,"reason":"valid","is_prebooking":true,"user":1}`.
- **Observed response:** HTTP 500 JSON with message `AttributeError: 'int' object has no attribute 'split'` (generated case API-0184 in [api-pytest-run.txt](evidence/api-pytest-run.txt)). The shared reservation read-back was unchanged.
- **Expected:** HTTP 422 with a field validation error for `user` being the wrong type; malformed input should not raise an uncaught server exception.
- **Likely root cause:** `Principal` parsing calls `.split()` on the supplied identifier and its error conversion handles `ValueError`, but not `AttributeError` from a non-string input. Source: `indico/modules/rb/schemas.py` (`booked_for_user = Principal(...)`) and `indico/util/user.py` (identifier parsing).
- **Severity:** High. **Likelihood 3 × impact 4 = 12/25.**
- **Proposed fix:** Validate that principal identifiers are strings before parsing and return the framework's normal schema validation error for all non-string JSON values. Add null, integer, object, and array cases.

### GitHub Issue draft

**Title:** Booking creation returns 500 when `user` is not a string

**Steps to reproduce**

1. Authenticate with a token allowed to create a booking.
2. `POST /rooms/api/booking/create` with valid fields and `"user": 1` (example body above).

**Expected:** HTTP 422 with a validation message identifying `user` as invalid.

**Actual:** HTTP 500 JSON with `AttributeError: 'int' object has no attribute 'split'`; no reservation was created.

**Severity:** High. **Priority:** P1.

---

## 4. Empty rejection reason reaches a database error and returns HTTP 500

- **Endpoint:** `POST /rooms/api/bookings/{booking_id}/reject`.
- **Reproduction:** For a pending booking the caller may moderate, send `POST /rooms/api/bookings/92/reject` with JSON `{"reason":""}` and `X-Requested-With: XMLHttpRequest`.
- **Observed response:** HTTP 500 JSON: `{"error":{"error_uuid":"59bff096-a630-494f-bbd6-14214e23f45d","message":"There was a database error while processing your request.","title":"Something went wrong"}}`. Generated cases API-0281 and API-0282 observed this, and the record read-back stayed unchanged. The raw transcript is linked above; source evidence is also in [spec-vs-actual-live.txt](evidence/spec-vs-actual-live.txt).
- **Expected:** HTTP 422 explaining the rejection reason must be non-empty. The model should never be asked to persist a value forbidden by its database constraint.
- **Likely root cause:** The action schema declares `reason` required but has no non-empty validator; the database check constraint rejects empty `rejection_reason` after the request reaches persistence.
- **Severity:** High. **Likelihood 3 × impact 4 = 12/25.**
- **Proposed fix:** Add an explicit non-empty validation to the reject request schema (and keep the database constraint as defense in depth); map validation failures to 422 before any state mutation.

### GitHub Issue draft

**Title:** Rejecting a booking with an empty reason returns a database HTTP 500

**Steps to reproduce**

1. Create a pending booking and authenticate as a room moderator.
2. Send `POST /rooms/api/bookings/92/reject` with `X-Requested-With: XMLHttpRequest` and JSON body `{"reason":""}`.

**Expected:** HTTP 422 with a field error that the reason must not be empty; booking state stays pending.

**Actual:** HTTP 500 JSON, title `Something went wrong`, message `There was a database error while processing your request.` The read-back showed no state change.

**Severity:** High. **Priority:** P1.

---

## 5. Repeating identical booking creates additional records

- **Endpoint:** `POST /rooms/api/booking/create`.
- **Reproduction:** Submit the same valid prebooking body twice sequentially, then repeat with two simultaneous requests.
- **Observed response:** Sequential calls both returned HTTP 200 with booking IDs **161** and **162**. Two rapid concurrent calls both returned HTTP 200 with IDs **163** and **164**. Each reservation could be read back. Exact request bodies and assertions are in [api-pytest-run.txt](evidence/api-pytest-run.txt).
- **Expected:** The Area 2 task explicitly asks that identical repeated requests create no duplicates. **This is a test-basis assumption**, not a guarantee found in the upstream API contract; the product owner should confirm idempotency is intended before treating this as an upstream defect.
- **Likely root cause:** The create endpoint has no idempotency key or duplicate-request guard, and each request independently inserts a new reservation. This is an inference from the observed distinct records.
- **Severity:** Moderate to High if clients retry after a timeout. **Likelihood 3 × impact 4 = 12/25.**
- **Proposed fix:** If idempotency is required, accept an idempotency key and enforce it transactionally with a unique constraint/recorded response. Do not deduplicate solely by matching time/room/reason because two intentional bookings may share those values.

### GitHub Issue draft

**Title:** Repeated identical booking create requests create duplicate reservations

**Steps to reproduce**

1. Authenticate with a token allowed to prebook.
2. Submit this body twice to `POST /rooms/api/booking/create`:

```json
{"start_dt":"2036-01-20T19:00:00","end_dt":"2036-01-20T20:00:00","repeat_frequency":"NEVER","repeat_interval":0,"room_id":1,"reason":"valid","is_prebooking":true}
```

3. Read both returned booking IDs back.

**Expected:** If create is intended to be idempotent, the retry returns the original booking or a documented duplicate response, and only one reservation exists. Confirm this product rule before implementation.

**Actual:** Both requests returned HTTP 200 and created distinct bookings (IDs 161 and 162 in the recorded run). Concurrent repeats also created IDs 163 and 164.

**Severity:** Moderate (elevated for retrying clients). **Priority:** P2, pending confirmation that idempotency is a product requirement.

---

## 6. Invalid booking-action paths return 405 instead of the expected not-found response

- **Endpoint:** `POST /rooms/api/bookings/{booking_id}/{action}`.
- **Reproduction:** Send `POST /rooms/api/bookings//approve` with JSON `{"reason":"valid"}` and `X-Requested-With: XMLHttpRequest`. Similar cases with missing, non-integer, or negative IDs behaved the same.
- **Observed response:** HTTP 405 JSON: `{"error":{"error_uuid":"2376b528-c7d6-4c14-b0a7-53c299ce0289","message":"The method is not allowed for the requested URL.","title":"Method Not Allowed"}}`. Transcript cases API-0244–API-0248 recorded 405 for malformed IDs where the test basis expected 404. The target valid booking remained unchanged.
- **Expected:** Consistent 404 for an invalid/nonexistent booking identifier; 405 should be reserved for a valid route with an unsupported HTTP method.
- **Likely root cause:** Flask route matching and the integer converter/action-constrained route distinguish malformed paths differently from the booking details route. The registered action route uses `<int:booking_id>` and `<any(approve,reject,cancel):action>` in `indico/modules/rb/blueprint.py`.
- **Severity:** Moderate. **Likelihood 3 × impact 2 = 6/25.**
- **Proposed fix:** Normalize malformed-resource routing to a documented 404 response (or document the intended 405 semantics consistently) and add route tests for empty, non-numeric, negative, and nonexistent IDs.

### GitHub Issue draft

**Title:** Malformed booking-action IDs return 405 while other missing booking resources return 404

**Steps to reproduce**

1. Send `POST /rooms/api/bookings//approve` with `X-Requested-With: XMLHttpRequest` and JSON `{"reason":"valid"}`.

**Expected:** HTTP 404 with the standard structured error body because the booking ID is invalid/missing.

**Actual:** HTTP 405 JSON with title `Method Not Allowed` and message `The method is not allowed for the requested URL.`

**Severity:** Moderate. **Priority:** P2.

---

## 7. Malformed timeline and booking-detail paths return empty 404 bodies

- **Endpoints:** `GET /rooms/api/rooms/{room_id}/timeline` and `GET /rooms/api/bookings/{booking_id}`.
- **Reproduction:** Send `GET /rooms/api/rooms//timeline?start_dt=2035-12-21T19%3A00%3A00&end_dt=2035-12-21T20%3A00%3A00` or `GET /rooms/api/bookings/` with `X-Requested-With: XMLHttpRequest`.
- **Observed response:** HTTP 404 with body `{}`. Cases API-0002–API-0006 and API-0231–API-0235 reproduced it. The OpenAPI contract describes a structured `ErrorEnvelope` for these 404 responses; the generated tests also failed their error-shape assertion.
- **Expected:** A stable JSON error body with an explanatory message and request/error identifier (or a documented HTML response when JSON was not requested).
- **Likely root cause:** These malformed paths fail Flask route matching before the Indico JSON error handler creates its usual error envelope.
- **Severity:** Low to Moderate (the status is correct, but clients get no useful details). **Likelihood 4 × impact 2 = 8/25.**
- **Proposed fix:** Ensure unmatched API routes use the API JSON error handler, including converter failures, and add route-level tests asserting status and body schema.

### GitHub Issue draft

**Title:** Malformed Room Booking API paths return an empty 404 JSON body

**Steps to reproduce**

1. Send `GET /rooms/api/bookings/` or the malformed timeline path above with `X-Requested-With: XMLHttpRequest`.

**Expected:** HTTP 404 with the documented JSON error envelope and an actionable message.

**Actual:** HTTP 404 with body `{}`.

**Severity:** Low. **Priority:** P3.

---

## Scope notes

- The repeated-create issue needs team confirmation because the API currently has no stated idempotency guarantee; duplicate prevention was explicitly required by the Area 2 testing task.
- Other observed contract differences—such as `X-Requested-With` values not being validated on successful requests, empty create reasons being rejected under the seeded `booking_reason_required=always` configuration, and explicit `user: null` being rejected—are documented in [suspected-defects.md](suspected-defects.md) but are not listed here as confirmed upstream defects. They are contract, test-basis, or configuration decisions.
- No live response or request value in this document is fabricated. Transient booking IDs and timestamps above are from the saved local test transcript and will differ after reseeding.
