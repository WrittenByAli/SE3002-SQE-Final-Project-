---
name: sqe-ci-gate
description: "GitHub Actions CI/CD quality gate for the SQE project: jobs, thresholds, branch protection, the documented fix PR (fails before, passes after) and the blocked PR. Use for \"CI failing\", \"add a job\", \"raise a threshold\", \"branch protection\", \"blocked PR\", \"fix PR\", \"deploy job\"."
---

# CI quality gate (Wania owns the workflow and gates; each area owner supplies a stable test command)

Workflow: `.github/workflows/ci.yml` (PRs to `main` + pushes to `main`).
| Job | Status | Gate |
|---|---|---|
| `harness` | ✅ exists | `tests/team/tools/check_harness.py` (structure, links, **no escape hatches**) + guard-hook self-test |
| `runner` | ✅ exists | Linux test-runner image builds (Py3.12, pinned Indico deps, mutmut) and Indico imports in it |
| `app-smoke` | ✅ exists | app stack builds, boots, seeds; the API answers with the seeded tokens (environment check, not a test deliverable) |
| `CI gate` | ✅ exists | aggregates the jobs above. **Branch protection requires this one check** |
| `unit` | ➕ Wania adds | team unit tests pass + rule-surface coverage ≥ thresholds |
| `mutation` | ➕ Wania adds | mutation score ≥ threshold (mutmut + two custom operators) |
| `sonarqube` | ➕ Wania adds | SonarQube metrics and justified quality gate |
| `api` | ➕ Wania integrates Fahima's suite | API tests against the booted stack |
| `e2e` / accessibility / security | ➕ Wania integrates Ali's suite | Playwright, axe, and security checks against the booted stack |
| `performance` | ➕ Wania integrates Ali's k6/recovery commands | Performance and recovery criteria meet documented thresholds |
| `deploy` | ➕ Wania adds | only on `main` after `CI gate`, e.g. publish reports to GitHub Pages (blocked by any failure) |
Add every new job to `needs:` of `CI gate`. Thresholds belong in `tests/team/quality-gates.yml` (ratchet: raise in the PR that earns it).

## Rules
- Never add `continue-on-error`, `|| true`, `set +e`, `--exit-zero`, or skip/xfail to go green. `if: always()` is allowed
  ONLY on the `ci-gate` aggregator (so a failed or skipped job turns the gate red instead of silently skipping it).
  `check_harness.py` fails the build if it finds them.
- Pin actions to a major version or SHA; cache Docker layers; keep total PR time < ~25 min.

## Documented fix PR (fails before, passes after)
1. Open an Issue (Defect template) with steps, expected/actual, severity, priority.
2. Branch `fix/<issue>-<slug>`. First commit = **failing test only** → push → CI red (link the run in the PR).
3. Second commit = the fix (in `indico/modules/rb/...`) → CI green. PR body: root cause, fix, both run links, `Fixes #<n>`.

## Blocked PR (pipeline correctly blocks)
Branch `demo/blocked-<slug>` with a harmful change, e.g. weaken an assertion so mutation drops below the gate, or change BR1
`<=`→`<` so the BVA test fails. Open the PR, let CI go red, keep it **unmerged**, and document which gate blocked it and why
that is correct. Branch protection must prevent merging (screenshot the disabled merge button).

## Branch protection (repo admin, once CI is green)
Already applied (requires `CI gate` + a PR before merging). Re-apply after changing the file:
`gh api -X PUT repos/WrittenByAli/SE3002-SQE-Final-Project-/branches/main/protection --input .github/branch-protection.json`
