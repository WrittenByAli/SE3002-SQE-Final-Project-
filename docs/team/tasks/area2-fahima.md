# Area 2: Fahima: API testing & test data generation (17 marks + leads)

Skills: `sqe-api-testing`, `sqe-openapi-generator`, `sqe-defect`, `sqe-test-management`. Agents: `test-case-designer`,
`evidence-verifier`, `viva-examiner`. Commands: `bash tests/team/run.sh env-reset` then `bash tests/team/run.sh api`.

Endpoints in scope (verified, see `docs/team/02-local-setup-verification.md` §API results):
`POST /rooms/api/booking/create`, `POST /rooms/api/bookings/{id}/approve|reject|cancel`, `GET /rooms/api/bookings/{id}`,
`GET /rooms/api/rooms/{room_id}/timeline`. Auth: `Authorization: Bearer <token>` from `tests/team/.env.test`.

## 1. Automated test data generation (7 marks)

- [ ] Write the **OpenAPI 3.0 spec** for the endpoints above: `openapi/rb.yaml`. Derive constraints from
      `CreateBookingSchema` (`indico/modules/rb/schemas.py`) and the handlers, not from guesswork. Add the business limits as
      vendor extensions where OpenAPI has no keyword (e.g. `x-booking-limit-days: 7`, `x-not-in-past: true`).
- [ ] Build **your generator** `tests/team/generator/generate.py`: reads the spec and emits, for every input,
      **EP classes** (valid + each invalid class) and **3-point BVA** values (just below / at / just above every limit) to
      `tests/team/generator/out/cases.json`, covering integer, enum, string, boolean, date-time, required/optional and
      the `x-` extensions. Ready for you: PyYAML/pytest/requests pinned in `tests/team/requirements-host.txt`.
- [ ] **API tests must consume the generator output** (parametrize from `cases.json`, never hand-typed values).
- [ ] **Change two constraints** in the spec (e.g. `booking_limit_days` 7→5, `reason` maxLength), regenerate, and show the diff
      in generated cases + which tests changed/failed → `docs/team/data-generation.md`. Expect a new spec in the viva.

## 2. API & integration testing (10 marks)

- [ ] **EP and 3-point BVA on every input** of `booking/create` (start_dt, end_dt, repeat_frequency, repeat_interval, room_id,
      reason, is_prebooking, user) and of approve/reject (reason, force), **one invalid value per test**.
- [ ] **Decision tables** for every rule with ≥2 conditions, at API level (who × state → status code + body).
- [ ] **State transitions**: every allowed transition + ≥1 disallowed from each state, via the approve/reject/cancel endpoints.
- [ ] **Rule rejections** (BR1 past start, BR1 limit, BR2 non-moderator, BR3 already decided) asserting status **and** message.
- [ ] **Repeated requests / no duplicates**: approve twice, reject twice, create the same request twice → assert no duplicate
      reservation (read back the timeline).
- [ ] **Read back shared records after success and after rejection** (GET booking + timeline).
- [ ] **API coverage criteria** (all endpoints × methods × status codes × parameters) → coverage table in `docs/team/api-testing.md`.
- [ ] **Endpoint weaknesses report** (start from the 4 findings in `02-local-setup-verification.md`: 418 status, three error
      shapes, HTML 404, vague overlap message). Each gets root cause, severity, risk link and fix.
- [ ] Ready for you: `tests/team/api/conftest.py` (Bearer-token clients `user1`/`mgr1`, `room_id`, collision-free
      `free_slot`, `booking_payload`) and `tests/team/api/pytest.ini` (markers `bva`, `ep`, `decision`, `state`, `smoke`).
      Write your tests as `tests/team/api/*_test.py`.
- [ ] Known defect to own: **HTTP 500 "Unsupported interval"** for `repeat_frequency` DAY/WEEK/MONTH with `repeat_interval: 0`
      (`docs/team/02-local-setup-verification.md`, finding 5). Model the field dependency in the spec and log it as an Issue.

## Leads (shared management)

- [ ] **Traceability matrix**: FR/BR → test cases (unit, API, E2E) → results → defects; requirements coverage % (`docs/team/traceability.md`).
- [ ] **Defect management**: every defect is a GitHub Issue (template "Defect"), with severity, priority, status and triage decision.
      **RCA (5 Whys + fishbone) for ≥2 major defects** with corrective + preventive actions. **Pareto by category**. (`docs/team/defects.md`)
- [ ] **Weekly progress report** against the plan with control actions and **GQM metrics**: defect density, requirements coverage,
      reopen rate (`docs/team/weekly/`). Use the `/loop` recipe in `docs/team/harness/loops.md`.

## Your 2 use cases

- [ ] UC-F1 User requests a room that needs confirmation, UC-F2 User cancels own pending booking. Template + automation
      in `tests/team/e2e/use-cases/`.

## Viva prep

- [ ] Rerun the BVA tests for `booking/create` live; explain how a value in `cases.json` became a test.
      Live task drill: "spec now says booking_limit_days = 5": regenerate, predict which tests flip.
