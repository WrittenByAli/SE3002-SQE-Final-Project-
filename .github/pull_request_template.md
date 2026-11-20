## What and why

<!-- One or two sentences. Link the issue: "Closes #12" (task) or "Fixes #14" (defect). -->
Closes #

**Area:** <!-- Area 1 / Area 2 / Area 3 / Shared --> &nbsp; **Rubric component:** <!-- e.g. White-box unit testing (16) -->

## How it was verified

<!-- Exact commands you ran and their result, e.g. `bash tests/team/run.sh api` -> 42 passed. Link raw evidence under docs/team/evidence/. -->
- [ ] Ran the relevant suite locally: `bash tests/team/run.sh <target>` → result:
- [ ] Evidence (raw tool output, unedited) committed under `docs/team/evidence/...` (if this PR reports numbers)

## Checklist (author)

- [ ] One task only, small and focused; branch name follows `docs/team/harness/github-workflow.md`
- [ ] Tests name the technique + rule ID; assertions check status **and** body **and** read-back state
- [ ] No secrets (`.env`, `.env.test`, tokens) and no CI escape hatches (`continue-on-error`, `|| true`, skip/xfail to pass)
- [ ] No quality-gate threshold lowered (or: justification below + approval from both other members)
- [ ] Traceability / risk register / task checklist updated if affected
- [ ] I can explain every line of this PR in the viva

## AI use

- [ ] No generative AI used in this PR
- [ ] AI used: row added to `docs/team/ai-use-record.md` (tool, purpose, output, **what I checked/changed**) and prompts saved in `docs/team/ai-prompts/<me>/`

## For the reviewer

<!-- Anything you want a second pair of eyes on. Reviewer: use the checklist in docs/team/harness/github-workflow.md#how-to-review-reviewer-checklist -->
