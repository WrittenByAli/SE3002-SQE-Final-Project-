"""Tests for the readable API case and decision-table generator."""

import json
import pytest

from tools.testgen.generate import (
    CASE_FIELDS,
    DEFAULT_RULES,
    DEFAULT_SPEC,
    MISSING,
    _boundary_values,
    build_api_cases,
    build_decision_cases,
    constraint_violations,
    field_cases,
    generate_cases,
    generate_decision_cases,
    read_yaml,
)


def test_api_generation_writes_only_ep_and_bva_cases(tmp_path):
    output = tmp_path / "cases.json"
    cases = generate_cases(DEFAULT_SPEC, output)
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert saved == cases
    assert cases
    assert all(set(case) == CASE_FIELDS for case in cases)
    assert {case["technique"] for case in cases} == {"EP", "BVA"}
    assert len({case["id"] for case in cases}) == len(cases)
    assert {(case["endpoint"], case["method"]) for case in cases} == {
        ("/rooms/api/rooms/{room_id}/timeline", "GET"),
        ("/rooms/api/timeline", "POST"),
        ("/rooms/api/booking/create", "POST"),
        ("/rooms/api/bookings/{booking_id}", "GET"),
        ("/rooms/api/bookings/{booking_id}/{action}", "POST"),
    }
    create_body = [
        case for case in cases
        if case["endpoint"] == "/rooms/api/booking/create" and case["field"] == "$body"
    ]
    assert any(case["class_or_point"] == "invalid:required" for case in create_body)
    assert any(case["class_or_point"] == "valid:object_fixture" for case in create_body)
    assert all(
        case["field"] != "recurrence_weekdays[]" or case["class_or_point"] != "valid:omitted"
        for case in cases
    )


@pytest.mark.parametrize(
    ("schema", "expected_classes"),
    [
        (
            {"type": "integer", "minimum": 2, "maximum": 5},
            {"invalid:minimum": "minimum", "invalid:maximum": "maximum"},
        ),
        (
            {"type": "string", "minLength": 2, "maxLength": 5},
            {"invalid:minLength": "minLength", "invalid:maxLength": "maxLength"},
        ),
        (
            {"type": "string", "enum": ["approve", "reject"]},
            {"invalid:enum": "enum"},
        ),
        (
            {"type": "string", "format": "date-time"},
            {"invalid:format": "format"},
        ),
        (
            {"type": "string", "pattern": "^abc$"},
            {"invalid:pattern": "pattern"},
        ),
        (
            {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
            {"invalid:uniqueItems": "uniqueItems"},
        ),
    ],
)
def test_ep_invalid_examples_break_one_constraint(schema, expected_classes):
    operation = {"responses": {"200": {}, "422": {}}}
    cases = field_cases(schema, "sample", True, "body", operation)

    for case in cases:
        label = case["class_or_point"]
        if not label.startswith("invalid:"):
            continue
        if label == "invalid:required":
            failures = constraint_violations(schema, MISSING, required=True)
            assert failures == ["required"]
        else:
            failures = constraint_violations(schema, case["value"])
            assert len(failures) == 1, (label, failures)
            if label in expected_classes:
                assert failures == [expected_classes[label]]

    actual_classes = {case["class_or_point"] for case in cases}
    assert set(expected_classes).issubset(actual_classes)
    assert "invalid:null" in actual_classes
    assert "invalid:type" in actual_classes


def test_required_and_optional_presence_classes():
    operation = {"responses": {"200": {}, "422": {}}}
    required = field_cases({"type": "integer"}, "count", True, "body", operation)
    optional = field_cases({"type": "integer"}, "count", False, "body", operation)

    assert any(case["class_or_point"] == "invalid:required" for case in required)
    assert any(case["class_or_point"] == "valid:omitted" for case in optional)


@pytest.mark.parametrize(
    ("schema", "expected_points"),
    [
        (
            {"type": "integer", "minimum": 2, "maximum": 5},
            {
                "below_minimum": (1, False),
                "at_minimum": (2, True),
                "above_minimum": (3, True),
                "below_maximum": (4, True),
                "at_maximum": (5, True),
                "above_maximum": (6, False),
            },
        ),
        (
            {"type": "number", "minimum": 1.0, "maximum": 2.0},
            {
                "below_minimum": (0.9, False),
                "at_minimum": (1.0, True),
                "above_minimum": (1.1, True),
                "below_maximum": (1.9, True),
                "at_maximum": (2.0, True),
                "above_maximum": (2.1, False),
            },
        ),
        (
            {"type": "string", "minLength": 2, "maxLength": 4},
            {
                "below_minLength": ("x", False),
                "at_minLength": ("xx", True),
                "above_minLength": ("xxx", True),
                "below_maxLength": ("xxx", True),
                "at_maxLength": ("xxxx", True),
                "above_maxLength": ("xxxxx", False),
            },
        ),
        (
            {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3},
            {
                "below_minItems": ([], False),
                "at_minItems": (["mon"], True),
                "above_minItems": (["mon", "tue"], True),
                "below_maxItems": (["mon", "tue"], True),
                "at_maxItems": (["mon", "tue", "wed"], True),
                "above_maxItems": (["mon", "tue", "wed", "thu"], False),
            },
        ),
    ],
)
def test_bva_has_below_at_and_above_for_each_limit(schema, expected_points):
    points = _boundary_values(schema, "field")

    assert dict(points) == {name: value for name, (value, _) in expected_points.items()}
    for name, value in points:
        assert (constraint_violations(schema, value) == []) is expected_points[name][1]


def test_decision_tables_cover_every_condition_combination_once():
    rules = read_yaml(DEFAULT_RULES)
    cases = build_decision_cases(rules)

    assert len(cases) == 80
    assert all(case["technique"] == "DECISION" for case in cases)
    for rule in rules["rules"]:
        conditions = rule["conditions"]
        assert len(conditions) >= 2
        expected_count = 1
        for choices in conditions.values():
            expected_count *= len(choices)
        rule_cases = [case for case in cases if case["field"] == rule["id"]]
        assert len(rule_cases) == expected_count
        assert len({json.dumps(case["value"]["conditions"], sort_keys=True) for case in rule_cases}) == expected_count


def test_decision_table_requires_exactly_one_matching_row():
    ambiguous = {
        "rules": [
            {
                "id": "R1",
                "endpoint": "/example",
                "method": "POST",
                "conditions": {"first": [False, True], "second": [False, True]},
                "outcomes": [
                    {
                        "when": {},
                        "expected_outcome": "default",
                        "expected_status": 200,
                        "expected_valid": True,
                    },
                    {
                        "when": {"first": True},
                        "expected_outcome": "specific",
                        "expected_status": 200,
                        "expected_valid": True,
                    },
                ],
            }
        ]
    }

    with pytest.raises(ValueError, match="matched 2 outcome rows"):
        build_decision_cases(ambiguous)


def test_cli_default_documents_have_the_expected_number_of_inputs():
    api_cases = build_api_cases(read_yaml(DEFAULT_SPEC))
    decision_cases = generate_decision_cases(DEFAULT_RULES)

    assert len(api_cases) == 284
    assert len(decision_cases) == 80
