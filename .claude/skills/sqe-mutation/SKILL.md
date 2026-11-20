---
name: sqe-mutation
description: "Mutation testing of the Indico business-rule surface with mutmut 3, custom rule-based mutation operators, and surviving-mutant analysis (equivalent / missing test / weak assertion). Use for \"mutation score\", \"surviving mutants\", \"kill mutants\", \"custom operator\", \"mutmut\"."
---

# Mutation analysis (Area 1, part of 8 marks)

Tooling ready: mutmut 3.8.1 in the Linux runner: `bash tests/team/run.sh mutation [args]` (e.g. `mutation run`,
`mutation results`, `mutation show <name>`). mutmut does not support native Windows, so always use the runner.
What you build (suggested design):
1. mutmut config (`[mutmut]` in `setup.cfg`: `paths_to_mutate` = the rule-surface files, tests = `tests/team/unit`). mutmut copies
   sources into `mutants/`; check that the tests really import the **mutated** copy (the runner installs Indico in editable mode).
   Restrict to rule-surface functions by passing mutant-name globs to `mutmut run`.
2. **custom rule-based mutants** in `tests/team/mutation/` + a script that applies each one, runs the unit suite and reverts it;
3. a gate script that combines both into a score and fails below the threshold in `tests/team/quality-gates.yml`.
Score = killed / (total − equivalent); keep every equivalent mutant with its reason in a file next to the operators.

## Custom operators (≥2 required, derived from the business rules)
Each operator is a (file, function, original snippet, mutated snippet, rule) entry in `custom_operators.py`. Examples:
- BR1 `ROR-limit`: `selected_period_days <= booking_limit_days` → `<` (off-by-one on the limit)
- BR2 `COND-swap`: `self.is_pending and` → `self.is_accepted and`
- BR3 `GUARD-drop`: remove `self.is_cancelled or` from `can_reject`
- BR4 `ADMIN-bypass`: `allow_admin and self.is_user_admin(user)` → `self.is_user_admin(user)`
A good custom operator models a **realistic developer mistake for that rule**. Explain this in the viva.

## Surviving-mutant analysis (≥15)
For each survivor: `mutmut show <name>` → classify:
- **equivalent**: no input can distinguish it (prove it; add to `equivalent.yml`);
- **missing test**: no test reaches that behaviour → write the test;
- **weak assertion**: a test reaches it but doesn't check the effect → strengthen the assertion.
Use the `mutant-analyst` agent for a first pass, then **verify each verdict yourself**. Table template:
`docs/team/templates/mutation-analysis.md` → `docs/team/mutation-analysis.md`. Re-run until all killable survivors are killed
(the `/loop` mutation-kill recipe in `docs/team/harness/loops.md`).

## Done when
Score reported with raw output saved to `docs/team/evidence/area1/`, ≥2 custom operators run in CI, ≥15 survivors analysed,
killable ones killed, threshold raised and justified in `docs/team/ci-quality-gate.md`.
