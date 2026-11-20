# Performance & recovery

## Limits (set BEFORE testing)
| Operation | Workload | p95 limit (ms) | Unexpected-failure limit | Why these limits suit the operation |
|---|---|---|---|---|

## Environment (same for every run)
Machine, CPU/RAM, Docker resources, Indico build/commit, starting data (`env-reset` before each run).

## Runs (≥60 s measured after ramp-up)
| Run | VUs | p95 (ms) | req/s | % unexpected failures | Meets limits? | Raw output |
|---|---|---|---|---|---|---|
| 1 | 1 | | | | | |
| 2 | 1 | | | | | |
| 3 | ≥5 | | | | | |
| 4 | ≥5 | | | | | |
Interpretation (run-to-run variance, 1 vs ≥5 VUs):

## Failure-and-recovery test
Operation · injected failure · state after failure · after restore + retry · duplicate check · test file · result
