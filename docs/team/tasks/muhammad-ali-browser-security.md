# Muhammad Ali: Use cases, usability, accessibility, security, and performance

Ali owns Area 3: browser use cases, usability/accessibility, defensive security, and performance/recovery. Wania owns the unit/white-box suite and CI; Fahima owns API and generated test data. All three members author and automate two use cases each.

## Browser framework and use cases

- [ ] Own the shared use-case template and Playwright framework under `tests/team/e2e/`, including browser setup, login helpers, fixtures, and common commands.
- [ ] Specify and automate two moderator use cases: approve a pending booking and reject a pending booking with a reason. Include preconditions, main flow, at least two alternatives, at least two exceptions, FR/BR links, and postconditions.
- [ ] Review the other four use-case specifications for completeness; each author owns their own test implementation and corrections.
- [ ] Ensure Playwright asserts the visible result and the postcondition for every flow. Keep all tests in the shared directory.

## Usability and accessibility

- [ ] Run two task-based browser checks, one per workflow. In one, submit a rejected value, check that the message explains how to correct it, then correct it and verify success.
- [ ] Add keyboard-only navigation to one task: assert focus order reaches required fields and submit, and that keyboard submission works.
- [ ] Run Lighthouse (accessibility, best practices, SEO) on each key use-case screen and a full axe-core scan via Playwright. Count a duplicate finding once.
- [ ] Record each finding's element, user impact, and proposed fix; fix one screen, rerun both tools, and compare before/after in `docs/team/accessibility.md`.

## Defensive security

- [ ] Map workflow routes/data and create the user/room-manager access matrix in `docs/team/security.md`.
- [ ] Automate at least four allowed/denied access decisions across both roles, including at least one allowed and one denied action.
- [ ] Run OWASP ZAP in passive mode while Playwright runs both workflows. Review at least two controls (such as cookie attributes, role checks, or CSRF) and verify against source/configuration.
- [ ] Run a dependency audit and record checked package names/versions. Document findings with evidence, impact, and correction—or the verified controls if no findings appear.

## Performance and recovery

- [ ] Choose one operation with the team and set justified p95 and unexpected-failure limits before testing.
- [ ] Run k6 with one VU and at least five concurrent VUs; run each setup twice for at least 60 measured seconds after ramp-up, using the same build, machine, and starting data.
- [ ] Record p95, requests/sec, failure percentage, environment, raw outputs, and comparison with limits in `docs/team/performance.md` and `docs/team/evidence/area3/`.
- [ ] Automate one controlled failure/recovery test for a state-changing operation. Verify persisted state after failure, restore/retry, and confirm the expected final state without duplicate records.

## Shared test management

- [ ] Participate with Fahima and Wania in the test plan, three-point estimates, risk register, traceability, weekly progress, defect management/RCA, and completion report. Report your own results, risks, findings, estimated and actual effort.

## Handoffs and completion

- [ ] Publish stable Playwright, accessibility, security, performance, and recovery commands/configuration to Wania for CI integration.
- [ ] Coordinate test accounts and windows with Fahima. Do not reset the database/file volumes during another member's run.
- [ ] Log AI assistance and preserve prompts. Keep raw evidence under `docs/team/evidence/area3/`; never fabricate or edit reports.
- [ ] Done when the shared framework runs all six use cases and the usability/accessibility, security, performance, and recovery evidence is reproducible.

## Viva preparation

- [ ] Rerun a browser test and explain each assertion. Explain one accessibility finding, one security control, the p95 target, and the recovery-state check.
