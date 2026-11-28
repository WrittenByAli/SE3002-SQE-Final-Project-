---
name: sqe-openapi-generator
description: "Write the OpenAPI 3.0 spec for the Room Booking endpoints and build/extend the generator that reads it and emits EP classes and 3-point BVA values for API tests; change two constraints and regenerate. Use for \"OpenAPI\", \"spec\", \"generator\", \"regenerate\", \"test data generation\", \"changed constraint\"."
---

# OpenAPI spec + test-data generator (Fahima owns, 7 marks)

Files: spec `openapi/rb.yaml` · generator `tests/team/generator/generate.py` · output `tests/team/generator/out/cases.json`
(committed so the diff after a spec change is visible) · loader `tests/team/generator/cases.py`.

## Spec rules
- Derive every constraint from code: `CreateBookingSchema` in `indico/modules/rb/schemas.py`, handlers in
  `indico/modules/rb/controllers/backend/bookings.py`. Cite the source line in a `description`.
- Use standard keywords where possible (`type`, `format: date-time`, `enum`, `minimum`, `maxLength`, `required`), and vendor
  extensions for business limits OpenAPI cannot express: `x-booking-limit-days`, `x-not-in-past`, `x-after: start_dt`.
- Document responses 200/403/418/422 with the real body shapes (see `sqe-api-testing`).

## Generator contract
`python tests/team/generator/generate.py openapi/rb.yaml -o tests/team/generator/out/cases.json`
Output: list of `{id, operation, field, technique: EP|BVA, partition: valid|invalid-<class>, value, expected: accept|reject, why}`.
- EP: one representative per valid class + one per invalid class (wrong type, missing required, out of enum, null…).
- BVA (3-point): for every numeric/length/date limit L: L−1, L, L+1 (or the smallest step for the type: 1 day, 1 char…).
- Deterministic (no randomness, or a fixed seed) so regeneration diffs are meaningful.
Support at least: integer, enum, string length, boolean, date-time, required/optional, and the `x-` extensions.

## Change two constraints (viva!)
1. Edit the spec (e.g. `x-booking-limit-days: 7 → 5`, `reason maxLength 300 → 100`).
2. Regenerate → `git diff tests/team/generator/out/cases.json` shows the moved boundaries.
3. Run the API tests: the cases at the old boundary now **expect** different outcomes. Show which fail against the unchanged app,
   and explain why (spec ≠ implementation → either update the app config or report a mismatch).
Record before/after in `docs/team/data-generation.md`.
