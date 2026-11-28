#!/usr/bin/env python3
"""Compare recorded Room Booking HTTP traffic with the Area 2 OpenAPI contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "openapi" / "openapi.yaml"
DEFAULT_LOG = ROOT / "tests" / "team" / "reports" / "api" / "http-traffic.jsonl"
DEFAULT_CASES = ROOT / "tools" / "testgen" / "out" / "cases.json"
DEFAULT_OUTPUT = ROOT / "docs" / "api" / "coverage-report.md"
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


def read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Expected an OpenAPI mapping in {path}")
    return data


def load_traffic(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"HTTP traffic log not found: {path}")
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {error}") from error
            if not isinstance(row, dict) or not isinstance(row.get("request"), dict):
                raise ValueError(f"Expected a request object at {path}:{line_number}")
            rows.append(row)
    return rows


def load_cases(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {case["id"]: case for case in data}


def resolve_local_ref(document: dict, node: dict) -> dict:
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"Only local OpenAPI references are supported: {ref}")
        node = document
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            node = node[part]
    if not isinstance(node, dict):
        raise ValueError("OpenAPI reference did not resolve to a mapping")
    return node


def all_operations(document: dict) -> dict[tuple[str, str], dict]:
    result = {}
    for path, path_item in document.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() in HTTP_METHODS and isinstance(operation, dict):
                result[(path, method.upper())] = operation
    return result


def match_path_template(template: str, actual: str) -> bool:
    """Match path parameters, allowing an empty segment for malformed-ID tests."""
    expression = re.escape(template)
    expression = re.sub(r"\\\{[^{}]+\\\}", r"[^/]*", expression)
    return re.fullmatch(expression, actual) is not None


def operation_for_row(row: dict, operations: dict, cases: dict[str, dict]):
    request = row["request"]
    method = str(request.get("method", "")).upper()
    case_id = row.get("case_id")
    if case_id in cases:
        case = cases[case_id]
        key = (case["endpoint"], case["method"].upper())
        if key in operations:
            return key
    path = request.get("path", "")
    matches = [key for key in operations if key[1] == method and match_path_template(key[0], path)]
    return matches[0] if len(matches) == 1 else None


def operation_input_fields(document: dict, path: str, operation: dict) -> set[str]:
    """Collect parameter and request-body input names, including array item inputs."""
    names: set[str] = set()
    path_item = document["paths"][path]
    parameters = list(path_item.get("parameters", [])) + list(operation.get("parameters", []))
    for parameter in parameters:
        parameter = resolve_local_ref(document, parameter)
        names.add(parameter["name"])

    def collect(schema: dict) -> None:
        schema = resolve_local_ref(document, schema)
        for branch in schema.get("anyOf", []) + schema.get("oneOf", []) + schema.get("allOf", []):
            collect(branch)
        for name, property_schema in schema.get("properties", {}).items():
            names.add(name)
            property_schema = resolve_local_ref(document, property_schema)
            if property_schema.get("type") == "array":
                names.add(name + "[]")
            collect(property_schema)

    request_body = operation.get("requestBody")
    if request_body:
        request_body = resolve_local_ref(document, request_body)
        for media_type in request_body.get("content", {}).values():
            collect(media_type.get("schema", {}))
    names.discard("")
    return names


def normalize_nullable(node):
    """Convert OpenAPI 3.0 nullable annotations to JSON Schema type unions."""
    if isinstance(node, list):
        return [normalize_nullable(item) for item in node]
    if not isinstance(node, dict):
        return node
    converted = {key: normalize_nullable(value) for key, value in node.items() if key != "nullable"}
    if node.get("nullable") and isinstance(node.get("type"), str):
        converted["type"] = [node["type"], "null"]
    return converted


def response_definition(document: dict, operation: dict, status: int):
    responses = operation.get("responses", {})
    response = responses.get(str(status), responses.get("default"))
    if response is None:
        return None, None, None
    response = resolve_local_ref(document, response)
    content = response.get("content", {})
    if not content:
        return response, None, None
    return response, content, None


def validate_response(document: dict, operation: dict, status: int, content_type: str, body):
    """Validate one logged response body against the declared OpenAPI response schema."""
    responses = operation.get("responses", {})
    response = responses.get(str(status), responses.get("default"))
    if response is None:
        return None, [f"HTTP {status} is not documented for this operation"]
    response = resolve_local_ref(document, response)
    content = response.get("content", {})
    if not content:
        return None, []
    media_type = content_type.split(";", 1)[0].strip().lower()
    selected = content.get(media_type)
    if selected is None and media_type.endswith("+json"):
        selected = content.get("application/json")
    if selected is None:
        selected = content.get("application/json") or next(iter(content.values()))
    schema = selected.get("schema")
    if schema is None:
        return None, []

    schema = normalize_nullable(schema)
    normalized_document = normalize_nullable(document)
    resolver = jsonschema.RefResolver.from_schema(normalized_document)
    validator = jsonschema.Draft4Validator(schema, resolver=resolver)
    errors = sorted(validator.iter_errors(body), key=lambda error: list(error.absolute_path))
    messages = []
    for error in errors[:3]:
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        messages.append(f"{location}: {error.message}")
    return schema, messages


def response_schema_refs(document: dict, operations: dict) -> dict[str, str]:
    refs = {}

    def collect(node, fallback: str) -> None:
        if isinstance(node, dict):
            if "$ref" in node:
                ref = node["$ref"]
                if ref.startswith("#/components/schemas/"):
                    name = ref.rsplit("/", 1)[-1]
                    refs[name] = ref
                else:
                    resolved = resolve_local_ref(document, node)
                    collect(resolved, fallback)
            else:
                for value in node.values():
                    collect(value, fallback)
        elif isinstance(node, list):
            for value in node:
                collect(value, fallback)

    for (path, method), operation in operations.items():
        for status, response in operation.get("responses", {}).items():
            response = resolve_local_ref(document, response)
            for media_type, media in response.get("content", {}).items():
                collect(media.get("schema"), f"{method} {path} {status} {media_type}")
    return refs


def pct(covered: int, total: int) -> str:
    return f"{100 * covered / total:.1f}%" if total else "n/a"


def analyze(document: dict, rows: list[dict], cases: dict[str, dict]) -> str:
    operations = all_operations(document)
    if not operations:
        raise ValueError("The OpenAPI document contains no operations")
    all_paths = sorted({path for path, _ in operations})
    expected_statuses = {
        key: {str(code) for code in operation.get("responses", {}) if code != "default"}
        for key, operation in operations.items()
    }

    mapped_rows = []
    unmapped = 0
    observed_operations = set()
    observed_statuses = defaultdict(set)
    observed_fields = defaultdict(set)
    seen_case_ids: set[str] = set()
    for row in rows:
        key = operation_for_row(row, operations, cases)
        if key is None:
            unmapped += 1
            continue
        mapped_rows.append((row, key))
        observed_operations.add(key)
        response = row.get("response") or {}
        status = response.get("status")
        if status is not None:
            observed_statuses[key].add(str(status))
        case_id = row.get("case_id")
        if case_id in cases:
            case = cases[case_id]
            if (case["endpoint"], case["method"].upper()) == key:
                seen_case_ids.add(case_id)
                field = re.sub(r"\[action=[^]]+\]", "", case["field"])
                if field != "$body":
                    observed_fields[key].add(field)

    observed_paths = {path for path, _ in observed_operations}
    operations_total = len(operations)
    statuses_total = sum(len(statuses) for statuses in expected_statuses.values())
    statuses_observed = sum(len(expected_statuses[key] & observed_statuses[key]) for key in operations)

    expected_fields = {key: operation_input_fields(document, key[0], operation)
                       for key, operation in operations.items()}
    all_expected_fields = sum(len(fields) for fields in expected_fields.values())
    covered_fields = sum(len(expected_fields[key] & observed_fields[key]) for key in operations)

    ep_cases = [case for case in cases.values() if case["technique"] == "EP"]
    bva_cases = [case for case in cases.values() if case["technique"] == "BVA"]
    seen_cases = [case for case in ep_cases + bva_cases if case["id"] in seen_case_ids]
    ep_valid = [case for case in ep_cases if case["expected_valid"]]
    ep_invalid = [case for case in ep_cases if not case["expected_valid"]]
    bva_points = bva_cases
    covered_ids = {case["id"] for case in seen_cases}
    valid_covered = sum(case["id"] in covered_ids for case in ep_valid)
    invalid_covered = sum(case["id"] in covered_ids for case in ep_invalid)
    bva_covered = sum(case["id"] in covered_ids for case in bva_points)

    required_schemas = response_schema_refs(document, operations)
    schema_stats = defaultdict(lambda: {"valid": 0, "invalid": 0})
    schema_errors = []
    checked_responses = 0
    valid_responses = 0
    for row, key in mapped_rows:
        response_info = row.get("response") or {}
        status = response_info.get("status")
        if status is None:
            continue
        headers = response_info.get("headers") or {}
        content_type = next((value for name, value in headers.items() if name.lower() == "content-type"), "")
        body = response_info.get("body")
        operation = operations[key]
        schema, errors = validate_response(document, operation, int(status), content_type, body)
        if schema is None:
            continue
        checked_responses += 1
        if errors:
            schema_errors.append((row, key, status, errors))
            for name, ref in required_schemas.items():
                if schema_ref_occurs(schema, ref):
                    schema_stats[name]["invalid"] += 1
        else:
            valid_responses += 1
            for name, ref in required_schemas.items():
                if schema_ref_occurs(schema, ref):
                    schema_stats[name]["valid"] += 1

    covered_schemas = {name for name, counts in schema_stats.items() if counts["valid"] + counts["invalid"]}
    required_status_gaps = {
        key: sorted(expected_statuses[key] - observed_statuses[key], key=lambda code: int(code))
        for key in operations
        if expected_statuses[key] - observed_statuses[key]
    }
    undocumented_statuses = {
        key: sorted(observed_statuses[key] - expected_statuses[key], key=lambda code: int(code))
        for key in operations
        if observed_statuses[key] - expected_statuses[key]
    }
    field_gaps = {key: sorted(expected_fields[key] - observed_fields[key])
                  for key in operations if expected_fields[key] - observed_fields[key]}
    missing_valid_ids = [case["id"] for case in ep_valid if case["id"] not in covered_ids]
    missing_invalid_ids = [case["id"] for case in ep_invalid if case["id"] not in covered_ids]
    missing_bva_ids = [case["id"] for case in bva_points if case["id"] not in covered_ids]
    missing_schemas = sorted(set(required_schemas) - covered_schemas)

    lines = [
        "# API coverage report",
        "",
        "Generated by `python tools/api_coverage.py` from the sanitized pytest HTTP traffic log and `openapi/openapi.yaml`.",
        "",
        "Coverage definitions: endpoint = OpenAPI path; HTTP method = path/method operation; status = documented status observed for that operation; field = OpenAPI input field with a generated case request recorded; EP/BVA = generated case IDs recorded on the test request; response schema = unique schema reference reached by a logged response and validated against the contract.",
        "",
        "## Summary",
        "",
        "| Criterion | Covered | Total | Coverage |",
        "|---|---:|---:|---:|",
        f"| Endpoints | {len(observed_paths)} | {len(all_paths)} | {pct(len(observed_paths), len(all_paths))} |",
        f"| HTTP method operations | {len(observed_operations)} | {operations_total} | {pct(len(observed_operations), operations_total)} |",
        f"| Documented operation/status pairs | {statuses_observed} | {statuses_total} | {pct(statuses_observed, statuses_total)} |",
        f"| Request fields | {covered_fields} | {all_expected_fields} | {pct(covered_fields, all_expected_fields)} |",
        f"| Valid EP cases | {valid_covered} | {len(ep_valid)} | {pct(valid_covered, len(ep_valid))} |",
        f"| Invalid EP cases | {invalid_covered} | {len(ep_invalid)} | {pct(invalid_covered, len(ep_invalid))} |",
        f"| 3-point BVA cases | {bva_covered} | {len(bva_points)} | {pct(bva_covered, len(bva_points))} |",
        f"| Response schema references | {len(covered_schemas)} | {len(required_schemas)} | {pct(len(covered_schemas), len(required_schemas))} |",
        f"| Logged response bodies valid against their schema | {valid_responses} | {checked_responses} | {pct(valid_responses, checked_responses)} |",
        "",
        f"HTTP exchanges logged: **{len(rows)}**; mapped to an OpenAPI operation: **{len(mapped_rows)}**; unmapped: **{unmapped}**.",
        "",
        "## Per-operation coverage",
        "",
        "| Operation | Methods | Documented statuses | Observed statuses | Missing statuses | Undocumented statuses | Fields | Schema-valid responses |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for key in sorted(operations):
        path, method = key
        statuses = sorted(expected_statuses[key], key=lambda code: int(code))
        observed = sorted(observed_statuses[key], key=lambda code: int(code))
        missing = sorted(expected_statuses[key] - observed_statuses[key], key=lambda code: int(code))
        undocumented = sorted(observed_statuses[key] - expected_statuses[key], key=lambda code: int(code))
        method_cell = method if key in observed_operations else "-"
        valid_count = sum(1 for row, operation_key in mapped_rows
                          if operation_key == key and row.get("response", {}).get("status") is not None
                          and not validate_response(
                              document, operations[key], int(row["response"]["status"]),
                              next((v for k, v in (row["response"].get("headers") or {}).items()
                                    if k.lower() == "content-type"), ""), row["response"].get("body")
                          )[1])
        total_schema_count = sum(1 for row, operation_key in mapped_rows
                                 if operation_key == key and row.get("response", {}).get("status") is not None
                                 and validate_response(
                                     document, operations[key], int(row["response"]["status"]),
                                     next((v for k, v in (row["response"].get("headers") or {}).items()
                                           if k.lower() == "content-type"), ""), row["response"].get("body")
                                 )[0] is not None)
        lines.append(
            f"| `{operations[key].get('operationId', path)}` | {method_cell} | {', '.join(statuses)} "
            f"| {', '.join(observed) or '-'} | {', '.join(missing) or '-'} "
            f"| {', '.join(undocumented) or '-'} "
            f"| {len(expected_fields[key] & observed_fields[key])}/{len(expected_fields[key])} "
            f"| {valid_count}/{total_schema_count} |"
        )

    lines.extend(["", "## Request-field gaps", ""])
    if field_gaps:
        for (path, method), fields in sorted(field_gaps.items()):
            lines.append(f"- `{method} {path}`: {', '.join(f'`{field}`' for field in fields)}")
    else:
        lines.append("None. Every OpenAPI input field had a generated request recorded.")

    lines.extend(["", "## Valid and invalid input-class gaps", ""])
    if missing_valid_ids:
        lines.append(f"- Valid EP cases not recorded ({len(missing_valid_ids)}): {', '.join(missing_valid_ids)}")
    if missing_invalid_ids:
        lines.append(f"- Invalid EP cases not recorded ({len(missing_invalid_ids)}): {', '.join(missing_invalid_ids)}")
    if missing_bva_ids:
        lines.append(f"- BVA points not recorded ({len(missing_bva_ids)}): {', '.join(missing_bva_ids)}")
    if not (missing_valid_ids or missing_invalid_ids or missing_bva_ids):
        lines.append("None. Every generated valid class, invalid class, and configured BVA point has a matching logged request.")

    lines.extend(["", "## Missing documented statuses", ""])
    if required_status_gaps:
        for (path, method), statuses in sorted(required_status_gaps.items()):
            lines.append(f"- `{method} {path}`: HTTP {', '.join(statuses)} not observed")
    else:
        lines.append("None. Every documented status code was observed for every operation.")

    lines.extend(["", "## Observed but undocumented statuses", ""])
    if undocumented_statuses:
        for (path, method), statuses in sorted(undocumented_statuses.items()):
            lines.append(f"- `{method} {path}`: HTTP {', '.join(statuses)} observed but absent from the OpenAPI responses.")
    else:
        lines.append("None. Every observed status code is documented for its operation.")

    lines.extend(["", "## Response schema gaps and mismatches", ""])
    if missing_schemas:
        lines.append(f"Schema references not sampled ({len(missing_schemas)}): {', '.join(f'`{name}`' for name in missing_schemas)}.")
    else:
        lines.append("Every unique response schema reference was sampled at least once.")
    if schema_errors:
        lines.append("")
        lines.append(f"Responses that failed their documented schema: **{len(schema_errors)}** (up to 25 shown).")
        for row, (path, method), status, errors in schema_errors[:25]:
            case_label = row.get("case_id") or row.get("test_id") or "unlabelled exchange"
            lines.append(f"- `{case_label}` - `{method} {path}` HTTP {status}: {errors[0]}")
    else:
        lines.append("No logged response body failed its documented schema.")

    lines.extend(["", "## Coverage data gaps", ""])
    if unmapped:
        lines.append(f"- {unmapped} HTTP exchange(s) did not match any OpenAPI path/method and did not carry a generated case ID.")
    if not unmapped:
        lines.append("Every logged request was matched to an OpenAPI operation.")

    lines.extend(["", "## Tests to close the gaps", ""])
    gap_exists = bool(field_gaps or missing_valid_ids or missing_invalid_ids or missing_bva_ids
                      or required_status_gaps or undocumented_statuses or missing_schemas or schema_errors or unmapped)
    if gap_exists:
        lines.append("Focused tests in `tests/team/api/room_booking_api_test.py` exercise insufficient OAuth scopes and the create-booking 404 path. Any remaining statuses or schema mismatches stay listed above; no assertion or OpenAPI response was changed to force coverage.")
    else:
        lines.append("No additional endpoint requests are needed for the listed criteria. Analyzer regression checks are in `tools/testgen/api_coverage_test.py`.")
    lines.append("")
    return "\n".join(lines)


def schema_ref_occurs(schema: dict, ref: str) -> bool:
    """Return whether a response schema uses a referenced component schema."""
    if isinstance(schema, dict):
        if schema.get("$ref") == ref:
            return True
        return any(schema_ref_occurs(value, ref) for value in schema.values())
    if isinstance(schema, list):
        return any(schema_ref_occurs(value, ref) for value in schema)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, default=DEFAULT_SPEC, help="OpenAPI 3 document")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="pytest HTTP JSONL log")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="generated EP/BVA case JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown report destination")
    args = parser.parse_args(argv)
    try:
        report = analyze(read_yaml(args.openapi), load_traffic(args.log), load_cases(args.cases))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"coverage analysis failed: {error}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
