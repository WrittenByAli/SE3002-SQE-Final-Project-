---
name: sqe-api-testing
description: "API and integration testing of Indico Room Booking endpoints with pytest + requests. EP and 3-point BVA on every input from generator output, decision tables, state transitions, rule rejections, repeated requests (no duplicates), read-back of shared records, API coverage criteria and endpoint weaknesses. Use for \"API test\", \"BVA\", \"EP\", \"state transition test\", \"idempotency\", \"endpoint weakness\"."
---

# API & integration testing (Area 2, 10 marks)

Run: `bash tests/team/run.sh env-reset && PYTHON=.venv/Scripts/python bash tests/team/run.sh api`.
Client + fixtures: `tests/team/api/conftest.py` (`user1`, `mgr1`, `room_id`, `free_slot`, `booking_payload`).

## Endpoints and observed contracts (v3.3.14)
| Call | Success | Rule rejection | Schema error | Access denied |
|---|---|---|---|---|
| `POST /booking/create` | 200 `{booking:{is_pending..}}` | 418 `{"message": ...}` | 422 `{"webargs_errors": ...}` | 403 `{"error": {...}}` |
| `POST /bookings/{id}/approve` | 200 `{booking}` | 418 already decided / `prebooking_collision` | n/a | 403 |
| `POST /bookings/{id}/reject` `{reason}` | 200 | 418 already cancelled/rejected | 422 missing reason | 403 |
| `GET /bookings/{id}` | 200 booking JSON | n/a | n/a | 404 **HTML** (weakness) |

## Test design rules
- **Inputs come from `tests/team/generator/out/cases.json`** (assignment: "API tests must use its output"):
  `@pytest.mark.parametrize('case', load_cases('booking_create', 'end_dt'), ids=lambda c: c['id'])`.
- **One invalid value per test** (all other fields valid). Assert status **and** message/body **and** read back the record.
- BVA: limit 7 days → end-start = 6 / 7 / 8 days (daily repeat: `repeat_frequency: "DAY", repeat_interval: 1`); start at
  yesterday / today / tomorrow (the grace period is `None` by default, so the check is by date).
- State transitions: matrix states {pending, accepted, rejected, cancelled} × actions {approve, reject, cancel(by user1)};
  every allowed one + ≥1 disallowed per state.
- Repeated requests: same approve twice → second 418, booking still accepted once; same create twice → second refused, timeline
  has one occurrence.
- Cross-workflow: after approval the slot is blocked for a new request; after rejection it is free again.

## API coverage criteria (report as a table in docs/team/api-testing.md)
endpoints covered, methods, status codes per endpoint (200/403/404/418/422), every parameter (EP+BVA), every content type
error, auth (missing/invalid token → ?). Missing token → observe and document.

## Endpoint weaknesses
Root cause, severity, risk-register link, proposed fix for each. Start from the 4 in `docs/team/02-local-setup-verification.md`.
