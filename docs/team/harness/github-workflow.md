# How we work on GitHub (read once, follow always)

Repo: https://github.com/WrittenByAli/SE3002-SQE-Final-Project-. Commit history is checked in the viva, so these rules protect your marks.

## The rules

1. **Nobody pushes to `main`.** `main` is protected: every change goes through a **pull request (PR)**.
2. **Every PR needs 1 approving review from another member**, plus the green **`CI gate`** check. You cannot approve your own PR.
3. **Commit your own work from your own account.** Set `git config user.name` / `user.email` to your GitHub identity once per clone.
   Never commit or push for someone else (the assignment checks individual commit history).
4. **One task = one issue = one branch = one PR.** Link the PR to its issue with `Closes #<n>` (or `Fixes #<n>` for defects).
5. **Small PRs** (ideally < 400 changed lines) get reviewed faster and better.
6. **AI use is disclosed in the PR** (checkbox + a row in `docs/team/ai-use-record.md`).
7. **No secrets** (`.env`, `tests/team/.env.test`, tokens), **no CI escape hatches**, **no lowering gates**. A hook and CI enforce this.

## Branch names

| Kind | Pattern | Example |
|---|---|---|
| Test work | `test/<area>-<topic>` | `test/a1-br3-can-cancel-mcc`, `test/a2-bva-create`, `test/a3-uc-w1` |
| Documents | `docs/<topic>` | `docs/risk-register` |
| Defect fix (the documented fix PR) | `fix/<issue>-<slug>` | `fix/14-repeat-interval-500` |
| CI / tooling | `ci/<topic>` | `ci/mutation-gate` |
| The deliberately blocked PR | `demo/blocked-<slug>` | `demo/blocked-weak-assertion` |

## Day-to-day flow

```bash
git switch main && git pull                       # start from the latest main
git switch -c test/a2-bva-create                  # new branch for ONE task (issue #12)
# ... work, run the relevant suite locally: bash tests/team/run.sh <target> ...
git add -p                                        # stage deliberately; never `git add .env*`
git commit -m "Add BVA tests for booking/create end_dt (#12)"
git push -u origin test/a2-bva-create
gh pr create --fill --base main                   # the PR template opens; fill every section
```
Then: request a reviewer (CODEOWNERS adds the area owner automatically), wait for `CI gate`, address comments with new commits
(don't force-push during review), and the **author merges** after approval + green CI ("Squash and merge" or "Create a merge commit";
both keep you as the author). The branch is deleted automatically.

Keeping your branch up to date: `git switch main && git pull && git switch - && git merge main` (or `git rebase main` before review).

## Who reviews whom (default rotation)

| Author | Reviewer | Why |
|---|---|---|
| Muhammad Ali (Area 1) | Fahima | API tests depend on the same rules Ali tests at unit level |
| Fahima (Area 2) | Wania | Wania's E2E/security tests use the same endpoints |
| Wania (Area 3) | Muhammad Ali | Ali wires every suite into CI |
| Shared documents | the two non-authors (≥1 approval required) | everyone is examined on test management |
If the default reviewer is unavailable for 24 h, any other member may review.

## How to review (reviewer checklist)

- [ ] Does the change do what the linked issue asks, and only that?
- [ ] Tests: technique and rule ID named; one behaviour per test; assertions check status **and** body **and** read-back state.
- [ ] No hand-typed numbers in reports. Every figure links to a raw artifact in `docs/team/evidence/`.
- [ ] No secrets, no `continue-on-error` / `|| true` / skip / xfail used to pass, no lowered threshold.
- [ ] AI use disclosed and the "what I checked" column is specific.
- [ ] Could the **author** explain this in the viva? Ask one question in the review if unsure.
Use GitHub's "Request changes" when something must change, "Approve" when it is ready, and comments for suggestions.

## Issues and the project board

- Tasks: issue template **Task** (one per checklist item in `docs/team/tasks/`), labelled `area:*` and assigned to the owner.
- Defects: issue template **Defect** (severity, priority, category, risk link, triage). See the `sqe-defect` skill.
- Milestones = weeks W1–W5 from `docs/team/tasks/README.md`.

## What CI checks on every PR (`.github/workflows/ci.yml`)

| Check | Meaning |
|---|---|
| `harness` | harness files valid (skills/agents front-matter, links, no escape hatches, guard-hook self-test) |
| `runner` | the Linux test runner image builds and Indico imports in it |
| `app-smoke` | the app stack builds, boots and seeds; the API answers with the seeded tokens |
| `CI gate` | all of the above passed. **The only check branch protection requires** |
Area 1 adds the test gates (unit + coverage, mutation, SonarQube, API, E2E) to `CI gate` as the project grows (`sqe-ci-gate` skill).
