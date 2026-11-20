---
name: sqe-a11y
description: "Automated usability and accessibility evaluation: Playwright task tests (rule rejection then correction), keyboard-only navigation test, Lighthouse (accessibility, best practices, SEO) and axe-core via @axe-core/playwright, deduplicated issue table, one screen fixed and before/after comparison. Use for \"accessibility\", \"Lighthouse\", \"axe\", \"keyboard test\", \"usability\"."
---

# Usability & accessibility (Area 3, 5 marks)

## Task tests (Playwright, `tests/team/e2e/tests/usability.spec.ts`)
1. Workflow A task: open booking screen as user1, book R1 → confirmation visible.
   **Rule rejection first**: choose a range longer than 7 days (BR1) or a past date → assert the error text tells the user what
   to correct → fix the value → success. (No error shown? Then the UI prevents it, so document that, and test the prevention.)
2. Workflow B task: mgr1 approves from the bookings list → confirmation visible.
3. Keyboard-only (in one of them): `page.keyboard.press('Tab')` loop, record `document.activeElement` labels, assert the order
   reaches the required fields then the submit button, then `Enter` submits.

## Scans
- axe: write `tests/team/e2e/tests/a11y.spec.ts` with `@axe-core/playwright` (installed in the e2e project) and save the JSON to
  `tests/team/reports/e2e/axe/`.
- Lighthouse (logged in): `npx lighthouse http://localhost:8081/rooms/ --only-categories=accessibility,best-practices,seo
  --output=json --output=html --output-path=docs/team/evidence/area3/lighthouse-<screen>-before --extra-headers=...`, or DevTools
  Lighthouse while logged in (save the JSON + HTML). Run on each use case's key screen.
- Merge: one row per issue; if both tools report the same element+rule, count it once and note "both".
  Columns: tool(s), rule, element (selector), user impact, severity, proposed fix, risk link.

## Fix + compare
Fix one screen (e.g. add labels/contrast in an rb template or your own HTML copy of the screen), rerun **both** tools, and put a
before/after table (scores + issue counts) in `docs/team/accessibility.md`. Keep raw before/after reports; never edit them.
