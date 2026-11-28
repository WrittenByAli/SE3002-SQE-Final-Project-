# Area 2 API test data generator

This small Python program reads the Area 2 OpenAPI file and creates test inputs. It does not call Indico or run the API tests. The generated cases are data for a test or a manual API check.

## Run it

From the repository root:

```powershell
python tools/testgen/generate.py
```

It writes:

- `tools/testgen/out/cases.json` for API input tests using equivalence partitioning (EP) and boundary value analysis (BVA).
- `tools/testgen/out/decision_cases.json` for every condition combination in `rules.yaml`.

To run the generator's own tests, use:

```powershell
python -m pytest -c tools/testgen/pytest.ini --noconftest tools/testgen/test_generate.py -q
```

The small pytest config keeps these utility tests separate from Indico's root pytest plugin, which needs the application's runtime dependencies.

## How the API cases are made

The generator visits every path and HTTP method in `openapi/openapi.yaml`. It reads path, query, and header parameters, request-body presence, and each request-body property. If a property is an array, it also visits the item schema (shown as `field[]`). For action bodies that use `anyOf`, each alternative is visited separately and its cases say which action they belong to.

EP groups values that should behave alike. A string enum gets a valid sample for each enum value. Booleans get `true` and `false`. Ordinary strings and arrays get useful empty and non-empty examples when the schema allows them. Optional fields get an omitted example; required fields get a missing example. Missing is written as `{"$missing": true}` so a test runner can leave that field out of the request.

For each declared input constraint, the generator tries to make one invalid value while keeping the other constraints valid. Examples include a string that is too short, a number below its minimum, an unknown enum value, or a malformed date-time. The generator checks its sample against the schema rules before adding it. If two constraints overlap so no isolated sample can be made, generation stops with an explanation instead of quietly writing a misleading case. A missing required field is checked as its own requiredness failure.

BVA creates three points around every explicit numeric minimum/maximum, string `minLength`/`maxLength`, and array `minItems`/`maxItems`: one just outside the limit, one exactly on it, and one just inside it. The cases' `expected_valid` value says whether that point satisfies the complete field schema. If another limit overlaps, a nearby point can fail that other limit too; the generator still records the boundary point and marks its validity from the full schema. A string cannot be shorter than `minLength: 0`, so the generator reports that unrepresentable boundary instead of pretending an empty string is shorter than zero.

The generator changes one field at a time. To execute a case, a test harness should start with a valid request for that endpoint, replace or omit the named field, and substitute any fixture marker. For example, `{"$fixture": "free_slot.start_rfc3339"}` means “use the valid start timestamp already prepared by the API test fixture.” `$fixture` values are intentionally not fake literal IDs or credentials.

Each API case includes an expected HTTP status selected from that operation's documented responses: success cases use its first documented 2xx response; invalid path identifiers prefer 404 (and an unknown action prefers 405); other invalid inputs use 422 when declared, otherwise the first declared 4xx response. These are OpenAPI expectations, not claims that the local app returned that status. Known differences are recorded in `docs/api/spec-vs-actual.md`; the generator does not rewrite its cases to hide those differences. The result describes each field in isolation and does not assert that its request will succeed when other fields, permissions, configuration, or business rules are invalid.

## How decision tables are made

`rules.yaml` names each rule, its conditions and possible values, plus outcome rows. The generator forms the Cartesian product: with two yes/no conditions there are four combinations; four yes/no conditions make sixteen. For every combination it finds the matching outcome row. A row may use `"*"` as a wildcard. Every combination must match exactly one row, otherwise generation stops. This prevents missing and overlapping decision rows from being silently accepted.

The rule file records its basis and preconditions. Some combinations come from source logic; some precedence and actor assumptions still need live verification. Treat these decision cases as test-basis expectations until verified, not as observed app results. In particular, `expected_valid` means the table predicts that the business rule permits processing; it does not mean a live API call has been made.

## Files and case shape

Both JSON files use the same case fields: `id`, `endpoint`, `method`, `field`, `technique`, `class_or_point`, `value`, `expected_status`, and `expected_valid`. API cases use `EP` or `BVA`; decision cases use `DECISION` and place the complete condition combination and outcome in `value`.

The expected status is useful for test planning, but generated values may require fixture setup such as a real seeded room, valid time slot, authenticated user, or reservation. The generator does not invent those records, tokens, API responses, or test results.
