# Static analysis and cyclomatic complexity

## Scan details

| Field | Value |
|---|---|
| SonarQube version | Community Build `25.11.0.114957` |
| Scan date | 2026-11-22 (date observed in the project session) |
| Branch | `dev/work-division` |
| Commit | SHA not captured by the dashboard; verify before citing as a reproducible baseline |
| Analyzed scope | Project-wide scan, approximately 33k lines; Python coverage report is narrower and must not be compared as if it covered every language |
| Raw evidence | `docs/team/evidence/area1/sonar-overview.png`, `technical-debt-sonarqube.png`, and `reservations-file-complexity-sonarqube.png`; scanner output/token metadata were not saved |

## Metrics

The values below are transcribed from the saved SonarQube overview screenshot. Where the screenshot does not show a metric, keep it marked as pending until a measure page or export provides it.

| Metric | Value | What it tells us about quality/risk | Action / risk link |
|---|---:|---|---|
| Cyclomatic complexity | 4,956 project-wide; 166 for `indico/modules/rb/models/reservations.py` in the file view | Number of independent code paths; high values need more careful tests and are harder to maintain | These are project/file totals, not the individual `can_cancel` score |
| Cognitive complexity | 2,349 project-wide | How difficult the code is to follow, especially with nested logic | Project-wide measure |
| Duplications | 0.6% | Repeated code that may need coordinated fixes | Review only in selected scope before treating as a project risk |
| Maintainability | Rating A; overview showed 393 | Maintainability issues | Project-wide count from overview |
| Reliability | Rating E; overview showed 229 | Reliability issues identified by SonarQube | Project-wide count from overview |
| Security and hotspots | Rating B; overview showed 5; hotspots reviewed 0.0% | Potential security weaknesses requiring review | Project-wide overview; hotspot review remains outstanding |
| Coverage | 12.5% Sonar overview | Portion of analyzed code reached by tests; distinguish the Room Booking rule surface from the module-wide number | Project-wide mixed-language denominator; use Python coverage report for the proposed rule-surface baseline |
| Technical debt | Overall code debt `4d 2h`; debt ratio `0.2%`; `indico/modules/rb` debt ratio `0.2%`; Maintainability rating A | Estimated effort to fix maintainability issues | Recorded from `technical-debt-sonarqube.png`; tests/team ratio shown as 0.0% |
| Ratings | Quality Gate Passed; Security B, Reliability E, Maintainability A | SonarQube's reliability, security, and maintainability assessment | Project-wide overview |

## Hand-calculated cyclomatic complexity

Function: `Reservation.can_cancel` (`indico/modules/rb/models/reservations.py`, around line 451 in the frozen source).

The control-flow graph below splits short-circuit Boolean checks into separate decision nodes and joins all return paths at one exit. It has `N = 20` nodes, `E = 28` edges, and one connected component (`P = 1`).

```mermaid
flowchart TD
  S([Start]) --> A{user is None?}
  A -- yes --> F1[return False]
  A -- no --> B{is_rejected?}
  B -- yes --> F2[return False]
  B -- no --> C{is_cancelled?}
  C -- yes --> F3[return False]
  C -- no --> D{is_archived?}
  D -- yes --> F4[return False]
  D -- no --> E{not is_pending?}
  E -- no --> G{is_owned_by user?}
  E -- yes --> H{no occurrence in cancel grace?}
  H -- yes --> F5[return False]
  H -- no --> G
  G -- yes --> T1[return True]
  G -- no --> I{is_booked_for user?}
  I -- yes --> T2[return True]
  I -- no --> J{allow_admin?}
  J -- no --> F6[return False]
  J -- yes --> R[return rb_is_admin user]
  F1 --> X([Exit])
  F2 --> X
  F3 --> X
  F4 --> X
  F5 --> X
  F6 --> X
  T1 --> X
  T2 --> X
  R --> X
```

| Nodes N | Edges E | Components P | Calculation `E − N + 2P` | Decision count + 1 | Sonar value |
|---:|---:|---:|---:|---:|---:|
| 20 | 28 | 1 | `28 − 20 + 2 = 10` | `9 + 1 = 10` | Sonar shows 166 for the whole `reservations.py` file; it does not expose the function-level score directly |

The nine control-flow decision nodes come from the initial `user is None` check, the three checks in the rejected/cancelled/archived expression, the pending/grace-period expression, the owner/booked-for expression, and the final admin checks. Sonar calculates complexity for individual functions but does not display those individual scores; the `166` is the aggregate for the file. It cannot be compared one-to-one with the hand-calculated `can_cancel` value of `10`. Report both values with their scope clearly labeled and explain this tool limitation.

## Evidence screenshots to capture

The overview, technical-debt, and source/complexity screenshots currently present under `docs/team/evidence/area1/` document the scan and source review. To make the report evidence complete, capture these details if available (plus the raw scan/report export):

1. **Project Overview:** already captured in `sonar-overview.png`; project name, branch, and Quality Gate are visible.
2. **Measures / Complexity:** overall complexity and the `reservations.py` file aggregate are recorded. Sonar does not directly display a function-level complexity score, so do not label the file total as `can_cancel`'s value.
3. **Measures / Duplications and Coverage:** overview values are recorded; capture the measure page with analyzed scope visible if possible.
4. **Issues:** capture counts/categories for code smells, bugs, vulnerabilities, and security hotspots.
5. **Maintainability:** technical debt and ratings are captured in `technical-debt-sonarqube.png` and the overview.

Use descriptive names such as `sonar-overview.png`, `sonar-complexity-can-cancel.png`, and `sonar-issues.png`. Screenshots supplement the report; they do not replace actual metrics or raw tool output.
