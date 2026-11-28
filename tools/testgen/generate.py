"""Build EP, BVA, and decision-table cases from the Area 2 OpenAPI files."""

from __future__ import annotations

import argparse
import itertools
import json
import re
from datetime import date, datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPEC = ROOT / "openapi" / "openapi.yaml"
DEFAULT_RULES = ROOT / "tools" / "testgen" / "rules.yaml"
DEFAULT_OUTPUT = ROOT / "tools" / "testgen" / "out" / "cases.json"
MISSING = {"$missing": True}
CASE_FIELDS = {
    "id",
    "endpoint",
    "method",
    "field",
    "technique",
    "class_or_point",
    "value",
    "expected_status",
    "expected_valid",
}


def read_yaml(path: Path) -> dict:
    """Read one YAML file and return its top-level mapping."""
    with path.open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return data


def resolve_ref(document: dict, node: dict) -> dict:
    """Resolve local OpenAPI references such as #/components/schemas/RoomId."""
    while isinstance(node, dict) and "$ref" in node:
        reference = node["$ref"]
        if not reference.startswith("#/"):
            raise ValueError(f"Only local OpenAPI references are supported: {reference}")
        node = document
        for part in reference[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            node = node[part]
    if not isinstance(node, dict):
        raise ValueError("An OpenAPI reference must resolve to a mapping")
    return node


def is_fixture_reference(value) -> bool:
    """Fixture placeholders stand for valid values supplied by API test fixtures."""
    if isinstance(value, dict) and "$fixture" in value:
        return True
    if isinstance(value, list):
        return any(is_fixture_reference(item) for item in value)
    if isinstance(value, dict):
        return any(is_fixture_reference(item) for item in value.values())
    return False


def format_is_valid(format_name: str, value: str) -> bool:
    """Check the OpenAPI formats used by this contract."""
    try:
        if format_name == "date-time":
            if not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
                value,
            ):
                return False
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        if format_name == "date":
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                return False
            date.fromisoformat(value)
            return True
        if format_name == "principal-identifier":
            return bool(re.fullmatch(r"(?:User:\d+:.+|ExternalUser:.+)", value))
    except ValueError:
        return False
    raise ValueError(f"No test-format checker is defined for OpenAPI format {format_name!r}")


def type_is_valid(expected_type: str | None, value) -> bool:
    """Check JSON types, taking care that Python bool is also an int subclass."""
    if expected_type is None:
        return True
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    raise ValueError(f"Unsupported OpenAPI type {expected_type!r}")


def constraint_violations(schema: dict, value, required: bool = False) -> list[str]:
    """Return the constraints a single value violates, stopping after a type error."""
    if value == MISSING:
        return ["required"] if required else []
    if is_fixture_reference(value):
        return []
    if value is None:
        return [] if schema.get("nullable", False) else ["null"]

    expected_type = schema.get("type")
    if not type_is_valid(expected_type, value):
        # Type checking is the first parsing step. An enum of strings does not add a
        # second effective error when the supplied JSON value is not a string.
        return ["type"]

    failures = []
    if expected_type in ("integer", "number"):
        if "minimum" in schema and value < schema["minimum"]:
            failures.append("minimum")
        if "maximum" in schema and value > schema["maximum"]:
            failures.append("maximum")

    if expected_type == "string":
        if "minLength" in schema and len(value) < schema["minLength"]:
            failures.append("minLength")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            failures.append("maxLength")
        if "enum" in schema and value not in schema["enum"]:
            failures.append("enum")
        if "format" in schema and not format_is_valid(schema["format"], value):
            failures.append("format")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            failures.append("pattern")

    if expected_type == "array":
        if "minItems" in schema and len(value) < schema["minItems"]:
            failures.append("minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            failures.append("maxItems")
        if schema.get("uniqueItems") and len(value) != len({json.dumps(x, sort_keys=True) for x in value}):
            failures.append("uniqueItems")
        item_schema = schema.get("items")
        if item_schema:
            for item in value:
                item_failures = constraint_violations(item_schema, item)
                failures.extend(f"items.{name}" for name in item_failures)

    if expected_type == "object":
        if "minProperties" in schema and len(value) < schema["minProperties"]:
            failures.append("minProperties")
        if "maxProperties" in schema and len(value) > schema["maxProperties"]:
            failures.append("maxProperties")

    if "enum" in schema and expected_type != "string":
        if value not in schema["enum"]:
            failures.append("enum")
    return failures


def _first_valid_string(schema: dict, field: str) -> str:
    """Find a small, readable string satisfying the field's other constraints."""
    choices = ["valid", "value", "x", "xx", "a", "ab", "abc", "123", "AA", "2026-12-01T10:00:00Z"]
    if schema.get("format") == "principal-identifier":
        choices = ["User:1:signature", "ExternalUser:opaque-id"] + choices
    if schema.get("format") == "date-time":
        choices = ["2030-01-01T10:00:00+00:00", "2026-12-01T10:00:00Z"] + choices
    minimum = schema.get("minLength", 0)
    choices.extend("x" * length for length in range(minimum, minimum + 8))
    for choice in choices:
        if constraint_violations(schema, choice) == []:
            return choice
    raise ValueError(f"Could not find a valid string sample for {field!r}")


def _valid_item(schema: dict, field: str):
    if schema.get("enum"):
        return schema["enum"][0]
    if schema.get("type") == "integer":
        if field.endswith("room_ids[]"):
            return {"$fixture": "room_id"}
        if field.endswith("skip_conflicts_with[]"):
            return {"$fixture": "booking_id"}
        return schema.get("minimum", 1)
    if schema.get("type") == "string":
        if schema.get("format") in ("date-time", "principal-identifier"):
            return {"$fixture": "valid_" + schema["format"].replace("-", "_")}
        return _first_valid_string(schema, field)
    if schema.get("type") == "boolean":
        return False
    if schema.get("type") == "object":
        return {}
    if schema.get("type") == "array":
        return []
    return "value"


def valid_examples(schema: dict, field: str) -> list[tuple[str, object]]:
    """Return one simple sample for each useful valid equivalence group."""
    value_type = schema.get("type")
    if schema.get("enum"):
        examples = [(f"valid:enum={value}", value) for value in schema["enum"]]
    elif value_type == "boolean":
        examples = [("valid:boolean=false", False), ("valid:boolean=true", True)]
    elif value_type in ("integer", "number"):
        if field in ("room_id", "booking_id"):
            sample = {"$fixture": field}
        else:
            sample = schema.get("minimum", schema.get("default", schema.get("maximum", 1)))
        examples = [("valid:number", sample)]
    elif value_type == "string":
        if schema.get("format") == "date-time":
            sample = {"$fixture": "free_slot." + ("end" if field.endswith("end_dt") else "start") + "_rfc3339"}
            examples = [("valid:format", sample)]
        elif schema.get("format") == "principal-identifier":
            examples = [("valid:format", {"$fixture": "booked_for_user_identifier"})]
        else:
            sample = _first_valid_string(schema, field)
            examples = [("valid:string", sample)]
            if not schema.get("minLength", 0) and "enum" not in schema and "format" not in schema and "pattern" not in schema:
                examples = [("valid:empty", ""), ("valid:nonempty", sample or "value")]
    elif value_type == "array":
        examples = [("valid:empty_array", [])]
        item_schema = schema.get("items", {})
        item = _valid_item(item_schema, field + "[]")
        sample = [item]
        if constraint_violations(schema, sample) == []:
            examples.append(("valid:nonempty_array", sample))
    elif value_type == "object":
        examples = [("valid:empty_object", {})]
        if schema.get("additionalProperties", False) is True:
            examples.append(("valid:nonempty_object", {"sample": "value"}))
    else:
        examples = [("valid:value", _valid_item(schema, field))]

    if schema.get("nullable", False):
        examples.append(("valid:null", None))
    return [(label, value) for label, value in examples if constraint_violations(schema, value) == []]


def _make_invalid_value(schema: dict, target: str, candidates: list) -> object:
    """Pick a value that violates only the named constraint."""
    for candidate in candidates:
        if constraint_violations(schema, candidate) == [target]:
            return candidate
    raise ValueError(f"No value isolates constraint {target!r} in schema {schema}")


def _array_of_length(schema: dict, length: int, field: str) -> list:
    if length < 0:
        raise ValueError(f"An array cannot have length {length} for {field!r}")
    if length == 0:
        return []
    item_schema = schema.get("items", {})
    values = []
    candidates = list(item_schema.get("enum", []))
    candidates.extend(["mon", "tue", "wed", "thu", "fri", "sat", "sun", 1, 2, 3, False, True, "a", "b"])
    for candidate in candidates:
        if constraint_violations(item_schema, candidate) == [] and (not schema.get("uniqueItems") or candidate not in values):
            values.append(candidate)
            if len(values) == length:
                break
    if len(values) != length:
        raise ValueError(f"Could not make {length} valid distinct items for {field!r}")
    return values


def _boundary_values(schema: dict, field: str) -> list[tuple[str, object]]:
    """Return below/at/above values for each explicit limit in a schema."""
    found = []
    value_type = schema.get("type")
    if value_type in ("integer", "number"):
        for key in ("minimum", "maximum"):
            if key not in schema:
                continue
            limit = schema[key]
            step = 1 if value_type == "integer" else 0.1
            below_label = "below_minimum" if key == "minimum" else "below_maximum"
            above_label = "above_minimum" if key == "minimum" else "above_maximum"
            values = [(below_label, limit - step), ("at_" + key, limit), (above_label, limit + step)]
            found.extend(values)
    elif value_type == "string":
        for key in ("minLength", "maxLength"):
            if key not in schema:
                continue
            limit = schema[key]
            if key == "minLength" and limit == 0:
                raise ValueError(f"No string can be shorter than minLength 0 for {field!r}")
            below_label = "below_minLength" if key == "minLength" else "below_maxLength"
            above_label = "above_minLength" if key == "minLength" else "above_maxLength"
            values = [
                (below_label, "x" * (limit - 1)),
                ("at_" + key, "x" * limit),
                (above_label, "x" * (limit + 1)),
            ]
            found.extend(values)
    elif value_type == "array":
        for key in ("minItems", "maxItems"):
            if key not in schema:
                continue
            limit = schema[key]
            below_label = "below_minItems" if key == "minItems" else "below_maxItems"
            above_label = "above_minItems" if key == "minItems" else "above_maxItems"
            values = [
                (below_label, _array_of_length(schema, limit - 1, field)),
                ("at_" + key, _array_of_length(schema, limit, field)),
                (above_label, _array_of_length(schema, limit + 1, field)),
            ]
            found.extend(values)

    return found


def field_cases(
    schema: dict,
    field: str,
    required: bool,
    location: str,
    operation: dict,
    include_presence: bool = True,
) -> list[dict]:
    """Create EP and BVA cases for one request field schema."""
    cases = []
    success_status = next(
        (int(status) for status in operation.get("responses", {}) if str(status).startswith("2")),
        200,
    )

    def rejection_status():
        responses = operation.get("responses", {})
        if location == "path":
            preferred = "405" if field == "action" else "404"
            if preferred in responses:
                return int(preferred)
        if "422" in responses:
            return 422
        for status in sorted(responses, key=lambda code: int(code) if str(code).isdigit() else 999):
            if str(status).startswith("4"):
                return int(status)
        raise ValueError(f"No documented rejection status for {field!r}")

    def add(technique, class_or_point, value, valid):
        cases.append({
            "endpoint": "",
            "method": "",
            "field": field,
            "technique": technique,
            "class_or_point": class_or_point,
            "value": value,
            "expected_status": success_status if valid else rejection_status(),
            "expected_valid": valid,
        })

    for label, value in valid_examples(schema, field):
        add("EP", label, value, True)

    if include_presence:
        if required:
            add("EP", "invalid:required", MISSING, False)
        else:
            add("EP", "valid:omitted", MISSING, True)

    if not schema.get("nullable", False):
        add("EP", "invalid:null", _make_invalid_value(schema, "null", [None]), False)

    value_type = schema.get("type")
    wrong_types = {
        "string": [1],
        "integer": ["not-an-integer"],
        "number": ["not-a-number"],
        "boolean": ["not-a-boolean"],
        "array": ["not-an-array"],
        "object": [[]],
    }
    if value_type in wrong_types:
        add("EP", "invalid:type", _make_invalid_value(schema, "type", wrong_types[value_type]), False)

    if value_type == "string":
        if "minLength" in schema:
            below = "" if schema["minLength"] == 1 else "x" * (schema["minLength"] - 1)
            add("EP", "invalid:minLength", _make_invalid_value(schema, "minLength", [below]), False)
        if "maximum" in schema:
            add("EP", "invalid:maximum", _make_invalid_value(schema, "maximum", [schema["maximum"] + 1]), False)
        if "maxLength" in schema:
            too_long = "x" * (schema["maxLength"] + 1)
            add("EP", "invalid:maxLength", _make_invalid_value(schema, "maxLength", [too_long]), False)
        if "enum" in schema:
            value = _make_invalid_value(schema, "enum", ["not-in-enum", "ZZZ", "", "invalid"])
            add("EP", "invalid:enum", value, False)
        if "format" in schema:
            invalid_samples = ["not-a-date", "not-a-principal", "invalid-format"]
            value = _make_invalid_value(schema, "format", invalid_samples)
            add("EP", "invalid:format", value, False)
        if "pattern" in schema:
            value = _make_invalid_value(schema, "pattern", ["!", "not-valid", "", "invalid"])
            add("EP", "invalid:pattern", value, False)

    if value_type in ("integer", "number"):
        if "minimum" in schema:
            add("EP", "invalid:minimum", _make_invalid_value(schema, "minimum", [schema["minimum"] - 1]), False)
        if "maximum" in schema:
            add("EP", "invalid:maximum", _make_invalid_value(schema, "maximum", [schema["maximum"] + 1]), False)

    if value_type == "array":
        for key, label in (("minItems", "minItems"), ("maxItems", "maxItems")):
            if key in schema:
                length = schema[key] - 1 if key == "minItems" else schema[key] + 1
                candidate = _array_of_length(schema, length, field)
                target = key
                candidate = _make_invalid_value(schema, target, [candidate])
                add("EP", f"invalid:{label}", candidate, False)
        if schema.get("uniqueItems"):
            item = _valid_item(schema.get("items", {}), field + "[]")
            duplicate = _make_invalid_value(schema, "uniqueItems", [[item, item]])
            add("EP", "invalid:uniqueItems", duplicate, False)

    for label, value in _boundary_values(schema, field):
        add("BVA", label, value, constraint_violations(schema, value) == [])

    return cases


def _with_item_cases(schema: dict, field: str, operation: dict, location: str) -> list[dict]:
    if schema.get("type") != "array" or "items" not in schema:
        return []
    return field_cases(schema["items"], field + "[]", False, location, operation, include_presence=False)


def _body_variants(document: dict, schema: dict):
    """Yield each anyOf/oneOf body schema and a short readable branch name."""
    schema = resolve_ref(document, schema)
    alternatives = schema.get("anyOf", schema.get("oneOf"))
    if alternatives:
        for alternative in alternatives:
            resolved = resolve_ref(document, alternative)
            reference_name = alternative.get("$ref", "").rsplit("/", 1)[-1]
            branch = reference_name.replace("BookingRequest", "").lower() or resolved.get("title", "branch").lower()
            yield branch, resolved
    else:
        yield "", schema


def _request_body_cases(required: bool, operation: dict) -> list[dict]:
    """Create presence and JSON-type cases for the request body as a whole."""
    cases = field_cases({"type": "object"}, "$body", required, "body", operation)
    for case in cases:
        if case["class_or_point"] == "valid:empty_object":
            case["class_or_point"] = "valid:object_fixture"
            case["value"] = {"$fixture": "valid_request_body"}
    return cases


def build_api_cases(document: dict) -> list[dict]:
    """Generate field-level EP and BVA cases for every OpenAPI operation input."""
    cases = []
    path_parameters = {}
    for endpoint, path_item in document.get("paths", {}).items():
        path_parameters[endpoint] = path_item.get("parameters", [])
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            all_parameters = list(path_parameters[endpoint]) + list(operation.get("parameters", []))
            for parameter in all_parameters:
                parameter = resolve_ref(document, parameter)
                schema = resolve_ref(document, parameter.get("schema", {}))
                field = parameter["name"]
                required = bool(parameter.get("required", schema.get("x-input-required", False)))
                field_cases_list = field_cases(schema, field, required, parameter.get("in", "query"), operation)
                for case in field_cases_list:
                    case["endpoint"] = endpoint
                    case["method"] = method.upper()
                    cases.append(case)
                for case in _with_item_cases(schema, field, operation, parameter.get("in", "query")):
                    case["endpoint"] = endpoint
                    case["method"] = method.upper()
                    cases.append(case)

            request_body = operation.get("requestBody")
            if request_body:
                request_body = resolve_ref(document, request_body)
                for case in _request_body_cases(bool(request_body.get("required", False)), operation):
                    case["endpoint"] = endpoint
                    case["method"] = method.upper()
                    cases.append(case)
                content = request_body.get("content", {})
                media = content.get("application/json") or next(iter(content.values()), {})
                body_schema = media.get("schema")
                if body_schema:
                    for branch, body_variant in _body_variants(document, body_schema):
                        required_properties = set(body_variant.get("required", []))
                        for name, property_schema in body_variant.get("properties", {}).items():
                            property_schema = resolve_ref(document, property_schema)
                            field = f"{name}[action={branch}]" if branch else name
                            required = bool(property_schema.get("x-input-required", name in required_properties))
                            field_cases_list = field_cases(property_schema, field, required, "body", operation)
                            for case in field_cases_list:
                                case["endpoint"] = endpoint
                                case["method"] = method.upper()
                                cases.append(case)
                            for case in _with_item_cases(property_schema, field, operation, "body"):
                                case["endpoint"] = endpoint
                                case["method"] = method.upper()
                                cases.append(case)

    for number, case in enumerate(cases, start=1):
        case["id"] = f"API-{number:04d}"
        case = {key: case[key] for key in ("id", "endpoint", "method", "field", "technique", "class_or_point", "value", "expected_status", "expected_valid")}
        cases[number - 1] = case
    return cases


def _matches_when(conditions: dict, when: dict) -> bool:
    return all(expected == "*" or conditions[name] == expected for name, expected in when.items())


def build_decision_cases(rules_document: dict) -> list[dict]:
    """Enumerate every condition combination and match it to one explicit decision row."""
    cases = []
    for rule in rules_document.get("rules", []):
        conditions = rule.get("conditions", {})
        if len(conditions) < 2:
            raise ValueError(f"Decision rule {rule.get('id')} needs at least two conditions")
        names = list(conditions)
        value_lists = [conditions[name] for name in names]
        for number, values in enumerate(itertools.product(*value_lists), start=1):
            combination = dict(zip(names, values))
            matches = [row for row in rule.get("outcomes", []) if _matches_when(combination, row.get("when", {}))]
            if len(matches) != 1:
                raise ValueError(
                    f"Decision rule {rule.get('id')} combination {combination} matched {len(matches)} outcome rows"
                )
            outcome = matches[0]
            cases.append({
                "id": f"{rule['id']}-{number:03d}",
                "endpoint": rule["endpoint"],
                "method": rule["method"].upper(),
                "field": rule["id"],
                "technique": "DECISION",
                "class_or_point": f"combination_{number:03d}",
                "value": {
                    "conditions": combination,
                    "expected_outcome": outcome["expected_outcome"],
                },
                "expected_status": int(outcome["expected_status"]),
                "expected_valid": bool(outcome["expected_valid"]),
            })
    return cases


def _write_cases(output_path: Path, cases: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def generate_cases(spec_path: Path = DEFAULT_SPEC, output_path: Path = DEFAULT_OUTPUT) -> list[dict]:
    """Read the OpenAPI document and write the EP/BVA API input cases."""
    spec = read_yaml(spec_path)
    if not str(spec.get("openapi", "")).startswith("3.0."):
        raise ValueError("This generator expects an OpenAPI 3.0.x document")
    cases = build_api_cases(spec)
    for case in cases:
        if set(case) != CASE_FIELDS:
            raise ValueError(f"Generated case has unexpected fields: {case}")
        if case["technique"] not in {"EP", "BVA"}:
            raise ValueError(f"Unexpected API test technique: {case['technique']}")
    _write_cases(output_path, cases)
    return cases


def generate_decision_cases(rules_path: Path = DEFAULT_RULES, output_path: Path | None = None) -> list[dict]:
    """Read rules.yaml, enumerate all rows, and optionally write the decision cases."""
    rules = read_yaml(rules_path)
    cases = build_decision_cases(rules)
    if output_path is not None:
        for case in cases:
            if set(case) != CASE_FIELDS:
                raise ValueError(f"Generated decision case has unexpected fields: {case}")
        _write_cases(output_path, cases)
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate EP, BVA, and decision-table cases from OpenAPI YAML.")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--decision-out",
        type=Path,
        default=DEFAULT_OUTPUT.parent / "decision_cases.json",
    )
    args = parser.parse_args()
    cases = generate_cases(args.spec, args.out)
    decisions = generate_decision_cases(args.rules, args.decision_out)
    print(f"Wrote {len(cases)} API cases to {args.out}")
    print(f"Wrote {len(decisions)} decision cases to {args.decision_out}")


if __name__ == "__main__":
    main()
