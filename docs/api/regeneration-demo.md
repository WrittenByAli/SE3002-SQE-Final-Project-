# OpenAPI regeneration demo

## What changed

Saved the baseline generated cases to [`cases-before-regeneration-demo.json`](evidence/cases-before-regeneration-demo.json) before changing the contract. The temporary spec changes were:

1. `CreateBookingRequest.properties.recurrence_weekdays.maxItems`: absent → `6`. The API takes distinct weekday names from the seven-day enum, so seven is the natural maximum. This demo deliberately changes the limit to six to show the generated maximum boundary and the resulting contract disagreement.
2. `RejectBookingRequest.properties.reason.minLength`: `1` → `2`. The documented business rule says a rejection reason must be non-empty. Requiring two characters is a deliberate temporary tightening so the one-character class moves across the boundary.

After regeneration, the spec was restored byte-for-byte from the branch baseline and the generator was rerun. The checked-in spec and `cases.json` are back to their baseline values (284 cases: 269 EP and 15 BVA). No temporary spec constraint remains.

## Generator output

The actual generator output while the temporary constraints were present was:

```text
Wrote 288 API cases to .../tools/testgen/out/cases.json
Wrote 80 decision cases to .../tools/testgen/out/decision_cases.json
after cases 288 EP 270 BVA 18
```

After restoring the spec and regenerating:

```text
Wrote 284 API cases to .../tools/testgen/out/cases.json
Wrote 80 decision cases to .../tools/testgen/out/decision_cases.json
restored cases 284 EP 269 BVA 15
```

## Readable old/new case diff

IDs below are the generator's IDs in each version. Adding cases shifts subsequent IDs, so compare by endpoint, field, technique, and class/point rather than treating an ID as a permanent rule identifier.

| Constraint | Baseline case | Temporary case | Change |
|---|---|---|---|
| Reject reason minLength 1 → 2 | `API-0281` invalid:minLength `""` → 422 | `API-0285` invalid:minLength `"x"` → 422 | The first invalid equivalence class moves from empty to one character. |
| Reject reason minLength 1 → 2 | `API-0282` below_minLength `""` → 422 | `API-0286` below_minLength `"x"` → 422 | Below-minimum BVA value changes from length 0 to length 1. |
| Reject reason minLength 1 → 2 | `API-0283` at_minLength `"x"` → 200 | `API-0287` at_minLength `"xx"` → 200 | At-minimum BVA value changes from length 1 to length 2. |
| Reject reason minLength 1 → 2 | `API-0284` above_minLength `"xx"` → 200 | `API-0288` above_minLength `"xxx"` → 200 | Above-minimum BVA value changes from length 2 to length 3. |
| Weekday maxItems absent → 6 | No maxItems cases | `API-0166` invalid:maxItems `[mon,tue,wed,thu,fri,sat,sun]` → 422 | A seven-day list becomes an invalid EP class. |
| Weekday maxItems absent → 6 | No maxItems BVA cases | `API-0168` below_maxItems list of 5 → 200 | Newly generated lower boundary neighbor. |
| Weekday maxItems absent → 6 | No maxItems BVA cases | `API-0169` at_maxItems list of 6 → 200 | Newly generated maximum boundary. |
| Weekday maxItems absent → 6 | No maxItems BVA cases | `API-0170` above_maxItems list of 7 → 422 | Newly generated upper boundary; same seven values as the invalid EP case. |

Other later case IDs shift by four because these changes add four generated cases. The saved baseline JSON and generator's temporary output above are the comparison evidence; the temporary output was not left in `cases.json`.

## API test attempt and interpretation

The targeted API command was attempted:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' tests/team/run.sh api -k 'API-0285 or API-0286 or API-0287 or API-0288 or API-0166 or API-0168 or API-0169 or API-0170' -q
```

It did **not** reach pytest or the application. The actual shell error was:

```text
bash: *** fatal error - NtCreateDirectoryObject(\BaseNamedObjects\msys-2.0S5-1888ae32e00d56aa): 0xC0000022
```

Therefore there are no live API test results for the temporary cases, and none are claimed here. The API behavior can be reasoned about from existing evidence, but this is not a replacement for running the cases:

- The baseline full API run recorded the one-character reject reason as `API-0283`, expected 200, and the response matched 200. Under temporary minLength 2, the same value becomes `API-0286`, expected 422. It is **expected to fail** if the live behavior remains the same; this is an inference from prior run evidence, not a run of the temporary case.
- The source validator checks weekday values against the weekday enum and has no maximum item count. The new seven-item maximum cases `API-0166` and `API-0170` are therefore **expected to reveal a mismatch** if the route accepts all seven distinct weekdays. This is a source-based prediction, not a live test result.

Existing API assertions were not edited to accommodate either temporary constraint. The earlier spec-change attempt left the OpenAPI file rewritten by PyYAML; that file was restored from the branch version and the generator was rerun. `git diff -- openapi/openapi.yaml tools/testgen/out/cases.json` then showed no diff.

## Commit status

The requested separate revert commit could not be made in this environment. The working spec and cases have been restored, but making commits requires the approval service, which reported its usage limit in the previous task. No commit or push is claimed. When Git write approvals are available, commit the temporary demo change and then make a separate revert commit only if you need the temporary history preserved; this working tree currently contains the restored files, not that two-commit history.
