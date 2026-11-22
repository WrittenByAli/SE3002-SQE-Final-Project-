# Fahima: API testing and data generation

Fahima owns Area 2: API/integration tests, OpenAPI, and generated test data. Her API suite covers the applicable endpoints and all BR1–BR4 behaviors represented by those endpoints. Wania owns unit/white-box tests and Ali owns browser-level testing. See `docs/team/01-scope-draft.md` for the shared rule map.

## OpenAPI and generated test data

- [ ] Maintain `openapi/rb.yaml` for create, approve, reject, cancel, booking read-back, and room-timeline endpoints. Derive schemas/constraints from the frozen Indico source and express project-specific constraints with `x-` extensions.
- [ ] Maintain `tests/team/generator/generate.py`. Generate valid and invalid equivalence partitions plus three-point boundary values for each applicable input into `tests/team/generator/out/cases.json`.
- [ ] Ensure API tests consume generated cases, use one invalid value per test, and assert response plus read-back state.
- [ ] Change two spec constraints, regenerate, and document changed cases and test impact in `docs/team/data-generation.md`.

## API and integration testing

- [ ] Own API tests in `tests/team/api/` for create, approve, reject, cancel, booking read-back, and room timeline.
- [ ] Apply equivalence partitioning and three-point BVA to every applicable input. Include decision tables, role permissions, rule rejections, every allowed state transition, and at least one disallowed transition from each state.
- [ ] Verify repeated requests do not create duplicates, and read back shared records after success and rejection. Record endpoint/method/status/parameter coverage in `docs/team/api-testing.md`.
- [ ] Verify the known API findings in `docs/team/02-local-setup-verification.md` against the running baseline. Document endpoint weaknesses and evidence; bring findings to the shared defect-management work.
- [ ] Save generator and API results in `docs/team/data-generation.md` and `docs/team/api-testing.md`.

## Your two use cases

- [ ] Specify and automate two user use cases in Ali's shared Playwright framework: (1) request a room requiring confirmation; (2) cancel one's own pending booking. Include preconditions, main flow, at least two alternatives, at least two exceptions, FR/BR links, and postconditions.

## Shared test management

- [ ] Participate with Ali and Wania in the test plan, three-point estimates, risk register, traceability, weekly reports, defect management/RCA, and completion report. Report your own results, risks, findings, estimated and actual effort.

## Handoffs and completion

- [ ] Publish the OpenAPI/generator command, API test command, and environment requirements to Wania for CI integration.
- [ ] Coordinate API accounts and fixtures with Ali. Do not reset the shared environment during another member's test run.
- [ ] Log AI assistance and preserve prompts. Keep generated inputs and raw API evidence reproducible; do not fabricate result numbers.
- [ ] Done when generated cases feed the API tests, all in-scope endpoints and techniques are covered, and your two use cases run in the shared framework.

## Viva preparation

- [ ] Rerun a generated API case and explain how the OpenAPI constraints produced it. Explain an endpoint coverage result, one rejected request, and the cross-workflow shared-record check.
