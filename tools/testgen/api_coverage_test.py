"""Unit tests for OpenAPI coverage accounting without a running Indico server."""

from tools.api_coverage import analyze, match_path_template


def _document():
    return {
        "openapi": "3.0.3",
        "paths": {
            "/widgets/{widget_id}": {
                "get": {
                    "operationId": "getWidget",
                    "parameters": [
                        {"name": "widget_id", "in": "path", "required": True,
                         "schema": {"type": "integer"}},
                        {"name": "verbose", "in": "query", "required": False,
                         "schema": {"type": "boolean"}},
                    ],
                    "responses": {
                        "200": {"description": "Found", "content": {"application/json": {
                            "schema": {"$ref": "#/components/schemas/Widget"}}}},
                        "404": {"description": "Missing", "content": {"application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}}}},
                    },
                }
            }
        },
        "components": {"schemas": {
            "Widget": {"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}},
            "Error": {"type": "object", "required": ["message"], "properties": {"message": {"type": "string"}}},
        }},
    }


def _case(case_id, field, technique, expected_valid):
    return {
        "id": case_id,
        "endpoint": "/widgets/{widget_id}",
        "method": "GET",
        "field": field,
        "technique": technique,
        "class_or_point": "valid" if expected_valid else "invalid",
        "value": 3,
        "expected_status": 200 if expected_valid else 422,
        "expected_valid": expected_valid,
    }


def _exchange(case_id, path, status, body):
    return {
        "case_id": case_id,
        "request": {"method": "GET", "path": path, "query": {}, "body": None},
        "response": {"status": status, "headers": {"content-type": "application/json"}, "body": body},
    }


def test_path_template_matches_empty_invalid_path_parameter():
    assert match_path_template("/widgets/{widget_id}", "/widgets/")
    assert not match_path_template("/widgets/{widget_id}", "/widgets/1/extra")


def test_analyzer_reports_uncovered_fields_statuses_and_schemas():
    cases = {
        "EP-VALID": _case("EP-VALID", "widget_id", "EP", True),
        "EP-INVALID": _case("EP-INVALID", "widget_id", "EP", False),
        "BVA-BELOW": {
            **_case("BVA-BELOW", "widget_id", "BVA", False),
            "class_or_point": "below_minLength",
        },
    }
    report = analyze(
        _document(),
        [_exchange("EP-VALID", "/widgets/3", 200, {"id": 3}),
         _exchange("EP-INVALID", "/widgets/3", 422, {"message": "invalid"}),
         _exchange("BVA-BELOW", "/widgets/0", 422, {"message": "below minimum"})],
        cases,
    )

    assert "| Endpoints | 1 | 1 | 100.0% |" in report
    assert "| HTTP method operations | 1 | 1 | 100.0% |" in report
    assert "| Documented operation/status pairs | 1 | 2 | 50.0% |" in report
    assert "| 3-point BVA cases | 1 | 1 | 100.0% |" in report
    assert "HTTP 422 observed but absent from the OpenAPI responses" in report
    assert "`GET /widgets/{widget_id}`: `verbose`" in report
    assert "HTTP 404 not observed" in report
    assert "Schema references not sampled (1): `Error`." in report
    assert "EP-VALID" not in report.split("## Valid and invalid input-class gaps", 1)[1].split("## Missing documented statuses", 1)[0]
