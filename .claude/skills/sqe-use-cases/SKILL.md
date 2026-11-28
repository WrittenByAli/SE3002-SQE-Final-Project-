---
name: sqe-use-cases
description: "Write use cases (preconditions, main flow, >=2 alternative and >=2 exception flows, postconditions) for the Indico Room Booking workflows and automate every flow with Playwright (Chromium), asserting the shown result and the postconditions. Use for \"use case\", \"alternative flow\", \"exception flow\", \"Playwright test\", \"e2e\"."
---

# Use cases + Playwright automation (Ali owns the shared framework; every member writes and automates 2)

Template: `docs/team/templates/use-case.md` → one file per UC in `docs/team/use-cases/UC-<ID>.md`.
Split (from `docs/team/tasks/README.md`): Ali UC-A1/A2 (moderator approve/reject), Fahima UC-F1/F2 (request/cancel),
Wania UC-W1/W2 (rule violation then fix / view status with keyboard).

## Writing the use case
- Trace to requirements: list FR-/BR- IDs at the top.
- Main flow = numbered user/system steps. Alternative flows still reach the goal (e.g. A1: user picks another free slot).
  Exception flows end without the goal (e.g. E1: start in past → error shown; E2: slot already approved → refused).
- Postconditions are **checkable** (booking state in API, slot shown as booked on the timeline).

## Automation (Playwright, `tests/team/e2e/`)
- Run: `bash tests/team/run.sh env-reset && bash tests/team/run.sh e2e`. Config: `playwright.config.ts` (Chromium only, HTML report).
- Login helper + API helper in `tests/team/e2e/support/` (log in through the UI; check postconditions through the API with tokens from `.env.test`).
- One `test()` per flow: `UC-F1 main`, `UC-F1 A1`, `UC-F1 E1`… so the report maps 1:1 to the spec.
- Assert what the user sees (`expect(page.getByText(...))`) **and** the postcondition (API read-back).
- Prefer role/label locators (`getByRole`, `getByLabel`). They also double as an accessibility check.
- Each test creates its own data in a unique future slot (no ordering dependencies).
