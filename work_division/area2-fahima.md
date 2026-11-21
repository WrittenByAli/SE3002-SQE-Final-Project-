# Member 2 — Fahima

## Focus

API testing and generated test data, plus static analysis and CI integration.

## Own these deliverables

- `openapi/rb.yaml`: document the in-scope room-booking API endpoints, schemas, and constraints from the source code.
- `tests/team/generator/generate.py` and `tests/team/generator/out/cases.json`: generate equivalence-partition and three-point boundary cases for applicable inputs, including project-specific `x-` constraints.
- `tests/team/api/`: parameterize API tests from generated cases. Cover the create, approve, reject, cancel, booking read-back, and room timeline endpoints, including permissions, state changes, rejected requests, and repeated requests.
- `docs/team/data-generation.md` and `docs/team/api-testing.md`: record the generator design, case coverage, API coverage, and results.
- Reproduce and document the known API findings in `docs/team/02-local-setup-verification.md`; file and track defects with evidence and severity.
- Run SonarQube and write `docs/team/static-analysis.md`, reporting the requested metrics for the agreed source and test scope.
- Own CI integration: add the SonarQube and API jobs, wire in Member 1's coverage/mutation commands and Member 3's E2E/performance commands, and make the required CI gate depend on the agreed jobs. Ask teammates for stable commands before wiring them in.
- Two use cases: user submits a room request and user cancels their own pending booking. Write the specifications and automate them using Member 3's Playwright framework.

## Shared lead responsibility

- Maintain the traceability matrix from FR/BR to unit, API, and E2E tests, results, and defects.
- Coordinate defect records, triage, root-cause analyses, and weekly progress reports. Each member supplies their own results and risks on schedule.

## Handoffs

- Agree on FR/BR IDs and request/response expectations with Member 1 before freezing the OpenAPI spec.
- Publish the generator command and API test command early so Member 1 can use them in CI.
- Coordinate with Member 3 on API fixtures and accounts; do not reset the shared test environment while another member is running tests.
- CI may integrate only after each owner documents a stable command and required environment variables.

## Done when

- Generated cases cover the documented input partitions and boundaries, and the API tests consume those cases.
- API results include positive and negative decisions, status and error assertions, and read-back checks.
- Static-analysis metrics and evidence are recorded.
- CI runs the agreed jobs and exposes a single required gate without bypasses.

