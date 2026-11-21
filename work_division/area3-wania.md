# Member 3 — Wania

## Focus

Browser use cases, usability and accessibility, defensive security, and performance/recovery.

## Own these deliverables

- The shared use-case template and Playwright framework under `tests/team/e2e/`, including browser setup, login helpers, and common fixtures.
- Review all six use cases for preconditions, main flow, at least two alternatives, at least two exceptions, postconditions, and links to FR/BR IDs.
- Automate your two assigned use cases in the shared test directory: one booking task and one manager task. Members 1 and 2 write and own their own two use-case tests using your framework.
- Run the two task-based usability checks, including one rejected input followed by a corrected successful submission.
- Add a keyboard-only navigation test, run axe-core and Lighthouse on the agreed screens, document findings, and fix one screen before rerunning the checks.
- Write the security access matrix and browser checks for allowed and denied actions across user and room-manager roles. Run a passive ZAP scan and a dependency audit; record evidence and findings.
- Write and run the k6 performance test using the agreed operation and thresholds. Run the failure-and-recovery test and verify persisted state and retry behavior.
- Maintain `docs/team/accessibility.md`, `docs/team/security.md`, and `docs/team/performance.md`, with raw reports in `docs/team/evidence/area3/`.
- Own the test account and browser-login guidance. Coordinate with the team to make seeded passwords comply with Indico's password policy so browser tests are not interrupted by a forced password-change screen.

## Shared lead responsibility

- Maintain the product and project risk register; map risks to techniques and measurable exit criteria.
- Draft the test-completion report using results and defect status supplied by all members. Make the release/hold recommendation against the agreed exit criteria.

## Handoffs

- Publish the Playwright directory, fixtures, login helper, and E2E command before the other members write browser tests.
- Agree on role accounts and password/reset behavior with Member 2, who owns API fixtures and CI integration.
- Give Member 2 the stable E2E, accessibility, security, and performance commands and required configuration for CI.
- Coordinate test windows with the other members; the reset script wipes local database and file volumes, so announce resets and avoid resetting during someone else's test run.

## Done when

- The shared framework runs all six use-case tests, with each member responsible for their own two tests.
- Usability, accessibility, security, performance, and recovery evidence is saved and summarized.
- Seeded test accounts can complete browser login without a forced password-change interruption.
- The risk register and completion report reflect actual results and open defects.

