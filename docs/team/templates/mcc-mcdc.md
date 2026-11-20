# MCC → MC/DC: critical module `<function>` (file:line)

Atomic conditions: A = … · B = … · C = … (list all; note short-circuit order).

## MCC table (every reachable combination; unreachable ones listed with the reason)
| Row | A | B | C | … | Outcome | Reachable? | Test name |
|---|---|---|---|---|---|---|---|

## MC/DC independence pairs (from the MCC rows above)
| Condition | Row x | Row y | Only this condition differs? | Outcome x / y |
|---|---|---|---|---|

Minimal MC/DC test set = rows: _ (N conditions → expect ≈ N + 1 rows)
