# Viva cheatsheet: change a constraint and regenerate API cases

Run from the repository root in PowerShell. This focused demo assumes Python dependencies are installed and the Docker app images already exist. On a warm local stack, it regenerates in seconds and selects only the affected API cases; the reset-and-seed fixture is the slow part.

## 1. Change the constraints

This example tightens the weekday list maximum to six and the rejection reason minimum length to two. It edits the YAML data and may reformat the file. The saved baseline copy is available at `docs/api/evidence/cases-before-regeneration-demo.json`; restore the spec after the demo with `git restore -- openapi/openapi.yaml` only when you have no other intended spec edits.

```powershell
python -c "from pathlib import Path; import yaml; p=Path('openapi/openapi.yaml'); d=yaml.safe_load(p.read_text(encoding='utf-8')); s=d['components']['schemas']; s['CreateBookingRequest']['properties']['recurrence_weekdays']['maxItems']=6; s['RejectBookingRequest']['properties']['reason']['minLength']=2; p.write_text(yaml.safe_dump(d,sort_keys=False,allow_unicode=True),encoding='utf-8')"
```

## 2. Regenerate and inspect

```powershell
python tools/testgen/generate.py
git diff -- tools/testgen/out/cases.json
```

The case generator reads the OpenAPI constraints. A change to minLength moves the invalid, below, at, and above values. A new maxItems adds an invalid class and below/at/above maximum cases. Case IDs can shift when cases are added; compare field and class/point as well as ID.

## 3. Run only affected API cases

```powershell
& 'C:\Program Files\Git\bin\bash.exe' tests/team/run.sh api -k 'API-0166 or API-0168 or API-0169 or API-0170 or API-0285 or API-0286 or API-0287 or API-0288' -q
```

The command resets and seeds the local test database before the API module. Keep Docker Desktop running. The focused run is intended to finish in under five minutes after the images have been built and Docker is warm; a cold first image build is not included. The demo run recorded in `regeneration-demo.md` could not reach pytest because Git Bash returned `NtCreateDirectoryObject ... 0xC0000022`, so do not quote its expected behavior as a measured result.

## 4. Restore the baseline

```powershell
git restore -- openapi/openapi.yaml
python tools/testgen/generate.py
git diff -- openapi/openapi.yaml tools/testgen/out/cases.json
```

No output from the final `git diff` means both the spec and generated cases match the current Git baseline. Do not edit the expected API statuses just to make a changed constraint pass; report a live mismatch as a suspected defect or a test-basis/spec decision.
