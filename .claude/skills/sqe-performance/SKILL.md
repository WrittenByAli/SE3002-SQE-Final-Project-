---
name: sqe-performance
description: "Performance and recovery testing with Grafana k6 OSS (1 VU and >=5 VUs, each twice, >=60s steady state, p95/req-s/error-rate vs pre-set limits) and an automated failure-and-recovery test for a state-changing operation with no duplicate records. Use for \"k6\", \"load test\", \"p95\", \"throughput\", \"recovery test\", \"failure injection\"."
---

# Performance & recovery (Ali owns, Area 3)

## Before testing: set limits (write them down first, with reasons)
e.g. `POST booking/create`: p95 ≤ 800 ms and < 1% unexpected failures at 1 VU; p95 ≤ 1500 ms and < 1% at 5 VUs.
Justify: interactive form submit, laptop-hosted Docker, the user tolerates about 1 s. "Unexpected" excludes the designed 418s
(e.g. a conflicting slot): use k6 `expected_response` / `check()` to separate them.

## k6 runs (your script in `tests/team/perf/`, e.g. `create_booking.js`)
- Scenarios: `ramping-vus` to N, then **≥60 s constant** at N; only measure the steady stage (tag it, threshold on the tag).
- N = 1 and N = 5 (or more). **Each twice.** `env-reset` before every run (same starting data), same build, same machine.
  Record machine specs + Docker resources + Indico version in `docs/team/performance.md`.
- Run: `bash tests/team/run.sh perf <script>.js` (k6 1.3.0 in Docker; `.env.test` provides `INDICO_BASE_URL`, tokens and
  `ROOM_ID`; inside the container use `K6_BASE_URL` = `http://host.docker.internal:8081`). Read the VU count from `__ENV`. Save the raw `--summary-export` JSON to
  `docs/team/evidence/area3/k6-<vus>vu-run<1|2>.json`.
- Report a table per run: p95 ms, req/s, % unexpected failures, pass/fail vs limits, then compare runs (variance) and 1 vs 5 VUs.

## Failure-and-recovery test (`tests/team/perf/recovery_test.py`, pytest)
State-changing operation = approve (or create). Inject: stop the DB right before the write
(`docker compose stop indico-postgres`), or use a test double that raises before commit. Then:
1. call → assert the error (5xx/connection error), 2. restore (`docker compose start indico-postgres`, wait healthy),
3. read back: state unchanged (still pending / no reservation), 4. retry → success, 5. assert exactly **one** reservation for the
slot (timeline) and the expected final state. Automate all steps; no manual clicking.
