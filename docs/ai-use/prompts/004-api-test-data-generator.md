Build tools/testgen/generate.py in Python. It reads openapi/openapi.yaml and writes tools/testgen/out/cases.json containing, for each input:
- EP classes: one valid class per valid group, and one invalid class per violated constraint (wrong type, missing, null/empty, below min, above max, too long, not in enum, bad format). Each invalid case violates exactly ONE constraint with everything else valid.
- 3-point BVA for every limit: just below, exactly at, just above (for both min and max).
Each case has: id, endpoint, method, field, technique (EP or BVA), class_or_point, value, expected_status, expected_valid.
Also add a decision-table generator that reads tools/testgen/rules.yaml, which lists the conditions of each business rule with two or more conditions, and outputs every condition combination with its expected outcome.
Add pytest tests for the generator itself and tools/testgen/README.md explaining the algorithm in plain words, because I must explain it in a viva. Keep the code simple and readable; no clever tricks.
