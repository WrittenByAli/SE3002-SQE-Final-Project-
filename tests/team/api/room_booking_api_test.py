"""Generated API, decision-table, state, and cross-workflow tests for Area 2."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta
from pathlib import Path

import pytest
import requests

from conftest import ApiClient, case_params, case_value, load_cases, read_back


ROOT = Path(__file__).resolve().parents[3]
CREATE = "/rooms/api/booking/create"
SINGLE_TIMELINE = "/rooms/api/rooms/{room_id}/timeline"
MULTI_TIMELINE = "/rooms/api/timeline"
BOOKING_DETAILS = "/rooms/api/bookings/{booking_id}"
BOOKING_ACTION = "/rooms/api/bookings/{booking_id}/{action}"
DECISION_FILE = ROOT / "tools" / "testgen" / "out" / "decision_cases.json"
MISSING = object()


def _decision_cases(rule_id: str | None = None) -> list[dict]:
    cases = json.loads(DECISION_FILE.read_text(encoding="utf-8"))
    return [case for case in cases if rule_id is None or case["field"] == rule_id]


def _decision_params() -> list:
    return [pytest.param(case, id=case["id"]) for case in _decision_cases()]


def _find_case(endpoint: str, field: str, class_or_point: str) -> dict:
    for case in load_cases(endpoint=endpoint, field=field):
        if case["class_or_point"] == class_or_point:
            return case
    raise AssertionError(f"No generated case for {endpoint} field {field} class {class_or_point}")


def _sample(request, endpoint: str, field: str, class_or_point: str):
    return case_value(_find_case(endpoint, field, class_or_point), request)


def _create_payload(request, *, recurrence_field: bool = False) -> dict:
    """Build a valid booking from generated field samples and the free-slot fixture."""
    endpoint = CREATE
    frequency_class = "valid:enum=WEEK" if recurrence_field else "valid:enum=NEVER"
    frequency = _sample(request, endpoint, "repeat_frequency", frequency_class)
    call_spec = getattr(request.node, "callspec", None)
    active_case = call_spec.params.get("case") if call_spec is not None else None
    if (
        not recurrence_field
        and active_case
        and active_case["endpoint"] == CREATE
        and active_case["field"] == "repeat_frequency"
        and active_case["expected_valid"]
        and active_case["value"] != {"$missing": True}
    ):
        frequency = case_value(active_case, request)
    interval = _sample(
        request,
        endpoint,
        "repeat_interval",
        "above_minimum" if frequency != "NEVER" else "valid:number",
    )
    body = {
        "start_dt": _sample(request, endpoint, "start_dt", "valid:format"),
        "end_dt": _sample(request, endpoint, "end_dt", "valid:format"),
        "repeat_frequency": frequency,
        "repeat_interval": interval,
        "room_id": _sample(request, endpoint, "room_id", "valid:number"),
        "reason": _sample(request, endpoint, "reason", "valid:nonempty"),
        "is_prebooking": _sample(request, endpoint, "is_prebooking", "valid:boolean=true"),
    }
    if recurrence_field:
        body["recurrence_weekdays"] = _sample(
            request, endpoint, "recurrence_weekdays", "valid:empty_array"
        )
        start = datetime.fromisoformat(body["start_dt"])
        body["end_dt"] = (start + timedelta(days=7)).isoformat(timespec="seconds")
    return body


def _timeline_params(request, endpoint: str) -> dict:
    return {
        "start_dt": _sample(request, endpoint, "start_dt", "valid:format"),
        "end_dt": _sample(request, endpoint, "end_dt", "valid:format"),
        "repeat_frequency": _sample(request, endpoint, "repeat_frequency", "valid:enum=NEVER"),
        "repeat_interval": _sample(request, endpoint, "repeat_interval", "valid:number"),
        "admin_override_enabled": _sample(
            request, endpoint, "admin_override_enabled", "valid:boolean=false"
        ),
    }


def _as_wire_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def _put_query_value(params: dict, field: str, value) -> None:
    if field.endswith("[]"):
        key = field[:-2]
        params[key] = [] if value is MISSING else ["" if value is None else value]
    elif field in ("recurrence_weekdays", "skip_conflicts_with") and isinstance(value, list):
        params[field] = value
    elif value is MISSING:
        params.pop(field, None)
    else:
        params[field] = "" if value is None else _as_wire_value(value)


def _response_json(response: requests.Response):
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        return None


def _safe_response_text(response: requests.Response) -> str:
    return re.sub(r'User:\d+:[^" ,}]+', "[redacted principal identifier]", response.text)


def _error_body_is_shaped(response: requests.Response) -> bool:
    body = _response_json(response)
    if body is None:
        return bool(response.text.strip())
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        return {"title", "message"}.issubset(body["error"])
    return isinstance(body, dict) and bool(body)


def _record_signature(response: requests.Response) -> dict:
    assert response.status_code == 200, (
        f"read-back failed: HTTP {response.status_code}: {response.text[:1000]}"
    )
    record = response.json()
    occurrence_states = []
    for group in (record.get("occurrences") or {}).values():
        for day_entries in group.values():
            for occurrence in day_entries:
                occurrence_states.append(
                    (
                        occurrence.get("start_dt"),
                        occurrence.get("end_dt"),
                        occurrence.get("state"),
                        occurrence.get("rejection_reason"),
                    )
                )
    return {
        "id": record.get("id"),
        "state": record.get("state"),
        "room_id": record.get("room_id"),
        "start_dt": record.get("start_dt"),
        "end_dt": record.get("end_dt"),
        "repetition": record.get("repetition"),
        "recurrence_weekdays": record.get("recurrence_weekdays"),
        "booking_reason": record.get("booking_reason"),
        "rejection_reason": record.get("rejection_reason"),
        "occurrences": sorted(occurrence_states),
    }


def _assert_unchanged(client: ApiClient, booking_id: int, before: dict) -> None:
    after = _record_signature(read_back(client, booking_id))
    assert after == before, f"rejected request changed the shared Reservation: before={before}, after={after}"


def _safe_request_description(method: str, path: str, body, params=None, headers=None) -> str:
    shown_body = body
    if isinstance(body, dict) and "user" in body:
        shown_body = dict(body)
        shown_body["user"] = "[redacted principal identifier]"
    shown_headers = {key: value for key, value in (headers or {}).items() if key.lower() != "authorization"}
    return json.dumps(
        {"method": method, "path": path, "params": params, "headers": shown_headers, "body": shown_body},
        default=str,
        sort_keys=True,
    )


def _assert_status(response: requests.Response, expected: int, request_description: str, case_id: str) -> None:
    response_text = _safe_response_text(response)
    assert response.status_code == expected, (
        f"{case_id}: expected HTTP {expected}; got HTTP {response.status_code}; "
        f"request={request_description}; response_headers={{'content-type': "
        f"{response.headers.get('Content-Type')!r}}}; response_body={response_text[:1600]!r}"
    )
    if response.status_code >= 400:
        assert _error_body_is_shaped(response), (
            f"{case_id}: rejection had no structured/non-empty body; "
            f"request={request_description}; response={_safe_response_text(response)[:1200]!r}"
        )


def _case_status(case: dict, value, room_id: int, anchor_id: int) -> int:
    """A schema-valid path ID still returns 404 when the seeded resource is absent."""
    if case["expected_valid"] and case["field"] == "room_id" and case["endpoint"] == SINGLE_TIMELINE:
        return 200 if str(value) == str(room_id) else 404
    if case["expected_valid"] and case["field"] == "booking_id":
        if case["value"] == {"$fixture": "booking_id"}:
            return 200
        return 200 if str(value) == str(anchor_id) else 404
    return case["expected_status"]


def _set_room(app_control, room_id: int, *, reservable=True, public=True, confirmation=True, permission=None):
    app_control.call(
        "room",
        room_id=room_id,
        reservable=reservable,
        public=public,
        confirmation=confirmation,
        permission=permission,
    )


@pytest.fixture
def valid_request_body(request):
    """Resolve the generator's whole-body fixture for the current operation."""
    case = request.node.callspec.params["case"]
    if case["endpoint"] == CREATE:
        return _create_payload(request)
    if case["endpoint"] == MULTI_TIMELINE:
        return {"room_ids": [_sample(request, MULTI_TIMELINE, "room_ids[]", "valid:number")]}
    action_endpoint = BOOKING_ACTION
    return {"reason": _sample(request, action_endpoint, "reason[action=approve]", "valid:nonempty")}


@pytest.fixture
def booked_for_user_identifier(app_control):
    return app_control.call("user_identifier")


@pytest.fixture
def booking_id(request, user1):
    """Create a fresh pending booking using valid values from cases.json."""
    payload = _create_payload(request)
    response = user1.post(CREATE, json=payload)
    assert response.status_code == 200, (
        f"booking fixture setup failed: HTTP {response.status_code}: {response.text[:1200]}"
    )
    booking = response.json()["booking"]
    _assert_success_readback(user1, booking["id"], "pending", payload)
    return booking["id"]


@pytest.fixture(scope="module")
def anchor_booking(user1, room_id):
    """A stable shared record used to check that read-only/rejected calls do not mutate state."""
    anchor_date = (datetime.now() + timedelta(days=2)).date()
    start = datetime.combine(anchor_date, time(hour=9))
    payload = {
        "start_dt": start.isoformat(timespec="seconds"),
        "end_dt": (start + timedelta(hours=1)).isoformat(timespec="seconds"),
        "repeat_frequency": _find_case(CREATE, "repeat_frequency", "valid:enum=NEVER")["value"],
        "repeat_interval": _find_case(CREATE, "repeat_interval", "valid:number")["value"],
        "room_id": room_id,
        "reason": _find_case(CREATE, "reason", "valid:nonempty")["value"],
        "is_prebooking": _find_case(CREATE, "is_prebooking", "valid:boolean=true")["value"],
    }
    response = user1.post(CREATE, json=payload)
    assert response.status_code == 200, (
        f"anchor setup failed: HTTP {response.status_code}: {response.text[:1200]}"
    )
    booking = response.json()["booking"]
    _assert_success_readback(user1, booking["id"], "pending", payload)
    return booking["id"]


@pytest.fixture(scope="module")
def admin_client(app_control, client_for_token):
    return client_for_token(app_control.call("admin_token"))


def _action_for_case(case: dict, value) -> str:
    field = case["field"]
    if field == "action" and case["expected_valid"]:
        return str(value)
    if "[action=reject]" in field:
        return "reject"
    if "[action=approve]" in field:
        return "approve"
    return "approve"


def _field_input(case: dict, request):
    value = case_value(case, request)
    missing = case["value"] == {"$missing": True}
    return (MISSING if missing else value)


def _build_api_request(case: dict, request, room_id: int, anchor_id: int):
    endpoint = case["endpoint"]
    field = case["field"]
    value = _field_input(case, request)
    method = case["method"]
    headers = {}
    if any(case["field"] == "X-Requested-With" for case in load_cases(endpoint=endpoint)):
        headers["X-Requested-With"] = _sample(
            request, endpoint, "X-Requested-With", "valid:enum=XMLHttpRequest"
        )
    params = None
    payload = None
    raw_body = False
    booking_target = anchor_id

    if endpoint == SINGLE_TIMELINE:
        route_room = room_id
        if field == "room_id":
            route_room = "" if value is MISSING else value
        path = SINGLE_TIMELINE.format(room_id=route_room)
        params = _timeline_params(request, endpoint)
        if field not in ("room_id", "X-Requested-With"):
            _put_query_value(params, field, value)
    elif endpoint == MULTI_TIMELINE:
        path = MULTI_TIMELINE
        params = _timeline_params(request, endpoint)
        payload = {
            "room_ids": [_sample(request, endpoint, "room_ids[]", "valid:number")]
        }
        if field == "$body":
            payload = value
            raw_body = True
        elif field == "room_ids":
            if value is MISSING:
                payload.pop("room_ids", None)
            else:
                payload["room_ids"] = value
        elif field == "room_ids[]":
            payload["room_ids"] = [] if value is MISSING else [value]
        elif field == "X-Requested-With":
            headers["X-Requested-With"] = None if value is MISSING else ("" if value is None else str(value))
        else:
            _put_query_value(params, field, value)
    elif endpoint == CREATE:
        path = CREATE
        body = _create_payload(request, recurrence_field=field.startswith("recurrence_weekdays"))
        if field == "$body":
            payload = value
            raw_body = True
        else:
            if field.endswith("[]"):
                name = field[:-2]
                body[name] = [] if value is MISSING else [value]
            else:
                name = field.split("[", 1)[0]
                if value is MISSING:
                    body.pop(name, None)
                else:
                    body[name] = value
            payload = body
        if payload and isinstance(payload, dict) and payload.get("is_prebooking", False) is False:
            _set_room(request.getfixturevalue("app_control"), room_id, confirmation=False)
        if field == "user":
            request_path = path
        else:
            request_path = path
        path = request_path
    elif endpoint in (BOOKING_DETAILS, BOOKING_ACTION):
        if endpoint == BOOKING_DETAILS:
            path = BOOKING_DETAILS.format(booking_id=anchor_id)
            if field == "booking_id":
                path = BOOKING_DETAILS.format(booking_id="" if value is MISSING else value)
            if field == "X-Requested-With":
                headers["X-Requested-With"] = None if value is MISSING else ("" if value is None else str(value))
            response_actor = request.getfixturevalue("user1")
            return response_actor, method, path, params, payload, raw_body, headers, booking_target

        action = _action_for_case(case, value)
        target_id = request.getfixturevalue("booking_id")
        booking_target = target_id
        if field == "booking_id":
            path_id = "" if value is MISSING else value
            path = BOOKING_ACTION.format(booking_id=path_id, action=action)
            try:
                parsed_id = int(path_id)
                booking_target = parsed_id if parsed_id == anchor_id else target_id
            except (TypeError, ValueError):
                booking_target = target_id
        elif field == "action":
            path_action = "" if value is MISSING else value
            path = BOOKING_ACTION.format(booking_id=target_id, action=path_action)
        else:
            path = BOOKING_ACTION.format(booking_id=target_id, action=action)

        if action == "cancel":
            response_actor = request.getfixturevalue("user1")
        elif action in ("approve", "reject"):
            response_actor = request.getfixturevalue("mgr1")
        else:
            response_actor = request.getfixturevalue("mgr1")
        if field.startswith("reason["):
            body_name = "reason"
            payload = {} if value is MISSING else {body_name: value}
        elif field.startswith("force["):
            payload = {"force": value} if value is not MISSING else {}
        elif field == "$body":
            payload = value
            raw_body = True
        elif action == "reject":
            payload = {"reason": _sample(request, endpoint, "reason[action=reject]", "valid:string")}
        elif action == "approve":
            payload = {"reason": _sample(request, endpoint, "reason[action=approve]", "valid:nonempty")}
        else:
            payload = None
        if field == "X-Requested-With":
            headers["X-Requested-With"] = None if value is MISSING else ("" if value is None else str(value))
        return response_actor, method, path, params, payload, raw_body, headers, booking_target
    else:
        raise AssertionError(f"Unhandled generated endpoint: {endpoint}")

    if endpoint in (SINGLE_TIMELINE, MULTI_TIMELINE) and field == "X-Requested-With":
        headers["X-Requested-With"] = None if value is MISSING else ("" if value is None else str(value))
    actor = request.getfixturevalue("user1")
    return actor, method, path, params, payload, raw_body, headers, booking_target


def _send(client: ApiClient, method: str, path: str, params, payload, raw_body: bool, headers):
    kwargs = {"params": params, "headers": headers}
    if raw_body:
        if payload is None:
            kwargs["data"] = "null"
            kwargs["headers"] = dict(headers, **{"Content-Type": "application/json"})
        elif payload is MISSING:
            pass
        else:
            kwargs["json"] = payload
    elif method.upper() == "POST" and payload is not None:
        kwargs["json"] = payload
    return client.request(method, path, **kwargs)


def _assert_success_readback(client: ApiClient, booking_id: int, expected_state: str, body: dict | None = None):
    response = read_back(client, booking_id)
    signature = _record_signature(response)
    assert signature["state"] == expected_state
    if body:
        assert signature["room_id"] == body["room_id"]
        frequency = body.get("repeat_frequency", "NEVER")
        frequencies = {"NEVER": 0, "DAY": 1, "WEEK": 2, "MONTH": 3}
        repetition = signature["repetition"]
        assert repetition[0] == frequencies[frequency]
        assert repetition[1] == body.get("repeat_interval", 0)
        requested_weekdays = body.get("recurrence_weekdays")
        if requested_weekdays:
            assert set(signature["recurrence_weekdays"] or ()) == set(requested_weekdays)

        stored_start = datetime.fromisoformat(signature["start_dt"])
        requested_start = datetime.fromisoformat(body["start_dt"])
        stored_end = datetime.fromisoformat(signature["end_dt"])
        requested_end = datetime.fromisoformat(body["end_dt"])
        # Weekly series with selected weekdays begin at the first matching day in the
        # requested range, so the stored reservation date can be later than its anchor.
        if requested_weekdays:
            assert stored_start.date() >= requested_start.date()
            weekday_names = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
            assert weekday_names[stored_start.weekday()] in requested_weekdays
        else:
            assert stored_start.date() == requested_start.date()
        assert stored_start.time() == requested_start.time()
        assert stored_end.time() == requested_end.time()
        assert signature["booking_reason"] == body.get("reason", "")
    return signature


@pytest.mark.parametrize("case", case_params())
@pytest.mark.timeout(900)
def test_generated_ep_and_bva_cases(case, request, room_id, user1, mgr1, anchor_booking):
    """Run every OpenAPI input EP/BVA case with the remaining fields valid."""
    anchor_before = _record_signature(read_back(user1, anchor_booking))
    actor, method, path, params, payload, raw_body, headers, affected_id = _build_api_request(
        case, request, room_id, anchor_booking
    )
    request_description = _safe_request_description(method, path, payload, params, headers)
    watch_id = affected_id if case["endpoint"] == BOOKING_ACTION else anchor_booking
    watch_before = _record_signature(read_back(user1, watch_id))

    try:
        response = _send(actor, method, path, params, payload, raw_body, headers)
    finally:
        if case["endpoint"] == CREATE and payload and isinstance(payload, dict) and payload.get("is_prebooking", False) is False:
            _set_room(request.getfixturevalue("app_control"), room_id, confirmation=True)

    actual_value = _field_input(case, request)
    expected_status = _case_status(case, actual_value, room_id, anchor_booking)
    if response.status_code >= 400:
        _assert_unchanged(user1, watch_id, watch_before)
    elif case["endpoint"] == CREATE:
        created = response.json()["booking"]
        assert {"id", "state", "room_id", "start_dt", "end_dt"}.issubset(created)
        state = "pending" if payload.get("is_prebooking", False) else "accepted"
        signature = _assert_success_readback(user1, created["id"], state, payload)
        assert signature["id"] == created["id"]
    elif case["endpoint"] == BOOKING_ACTION:
        result = response.json()
        assert isinstance(result.get("booking"), dict)
        new_state = result["booking"]["state"]
        signature = _assert_success_readback(user1, affected_id, new_state)
        assert signature["state"] == new_state
    elif case["endpoint"] == BOOKING_DETAILS:
        result = response.json()
        assert {"id", "state", "room_id", "start_dt", "end_dt"}.issubset(result)
        signature = _assert_success_readback(user1, result["id"], result["state"])
        assert signature["id"] == result["id"]
    else:
        result = response.json()
        assert {"availability", "date_range"}.issubset(result)
        _assert_unchanged(user1, anchor_booking, anchor_before)
    _assert_status(response, expected_status, request_description, case["id"])


@pytest.mark.parametrize("decision", _decision_params())
def test_decision_table_cases(decision, request, room_id, user1, mgr1, app_control, admin_client):
    """Exercise all generated condition combinations for the six multi-condition rules."""
    rule = decision["field"]
    conditions = decision["value"]["conditions"]
    anchor = request.getfixturevalue("anchor_booking")
    anchor_before = _record_signature(read_back(user1, anchor))
    expected = decision["expected_status"]
    method = decision["method"]
    response = None
    body = None
    actor = user1
    booking = None
    action = "approve"

    if rule == "BR1":
        body = _create_payload(request)
        start = datetime.fromisoformat(body["start_dt"])
        if not conditions["start_not_in_past"]:
            start -= timedelta(days=1)
        body["start_dt"] = start.isoformat(timespec="seconds")
        if conditions["within_booking_limit"]:
            body["end_dt"] = (start + timedelta(hours=1)).isoformat(timespec="seconds")
        else:
            body["end_dt"] = (start + timedelta(days=8, hours=1)).isoformat(timespec="seconds")
        response = user1.post(CREATE, json=body)
        request_description = _safe_request_description(method, CREATE, body)
        if response.status_code >= 400:
            _assert_unchanged(user1, anchor, anchor_before)
        else:
            created_id = response.json()["booking"]["id"]
            _assert_success_readback(user1, created_id, "pending", body)
        _assert_status(response, expected, request_description, decision["id"])
        return

    if rule in ("BR4_DIRECT", "BR4_PREBOOK"):
        direct = rule == "BR4_DIRECT"
        permission = "book" if direct else "prebook"
        _set_room(
            app_control,
            room_id,
            reservable=conditions["is_reservable"],
            public=conditions["is_public"],
            confirmation=conditions["needs_confirmation"],
            permission=permission if conditions.get("has_explicit_book_right", conditions.get("has_explicit_prebook_right")) else None,
        )
        body = _create_payload(request)
        body["is_prebooking"] = not direct
        try:
            response = user1.post(CREATE, json=body)
        finally:
            _set_room(app_control, room_id)
        request_description = _safe_request_description(method, CREATE, body)
        if response.status_code >= 400:
            _assert_unchanged(user1, anchor, anchor_before)
        else:
            created_id = response.json()["booking"]["id"]
            state = "pending" if not direct else "accepted"
            _assert_success_readback(user1, created_id, state, body)
        _assert_status(response, expected, request_description, decision["id"])
        return

    if rule == "BR2":
        booking = request.getfixturevalue("booking_id")
        if not conditions["is_pending"]:
            _approve(mgr1, booking)
        actor = mgr1 if conditions["can_moderate"] else user1
        action = "approve"
        body = {"reason": _sample(request, BOOKING_ACTION, "reason[action=approve]", "valid:nonempty")}
    elif rule == "BR3_REJECT":
        booking = request.getfixturevalue("booking_id")
        if conditions["is_terminal_state"]:
            _cancel(user1, booking)
        actor = mgr1 if conditions["can_moderate"] else user1
        action = "reject"
        body = (
            {"reason": _sample(request, BOOKING_ACTION, "reason[action=reject]", "valid:string")}
            if conditions["reason_present"]
            else {}
        )
    elif rule == "BR3_CANCEL":
        state = conditions["state"]
        booking = request.getfixturevalue("booking_id")
        if state == "accepted":
            _approve(mgr1, booking)
            if not conditions["within_cancel_grace_period"]:
                _set_accepted_booking_outside_cancel_grace(app_control, booking)
        elif state == "rejected":
            _reject(mgr1, booking, request)
        elif state == "cancelled":
            _cancel(user1, booking)
        if conditions["is_booker_or_booked_for"]:
            actor = user1
        elif conditions["is_rb_admin"]:
            actor = admin_client
        else:
            actor = mgr1
        action = "cancel"
        body = None
    else:
        raise AssertionError(f"Unknown decision rule: {rule}")

    before = _record_signature(read_back(user1, booking))
    path = BOOKING_ACTION.format(booking_id=booking, action=action)
    response = actor.post(path, json=body) if body is not None else actor.post(path)
    request_description = _safe_request_description(method, path, body)
    if response.status_code >= 400:
        _assert_unchanged(user1, booking, before)
    else:
        after = _record_signature(read_back(user1, booking))
        expected_state = {
            "BR2": "accepted",
            "BR3_REJECT": "rejected",
            "BR3_CANCEL": "cancelled",
        }[rule]
        assert after["state"] == expected_state
    _assert_status(response, expected, request_description, decision["id"])


def _approve(client: ApiClient, booking_id: int) -> None:
    response = client.post(BOOKING_ACTION.format(booking_id=booking_id, action="approve"), json={})
    assert response.status_code == 200, f"setup approve failed: {response.status_code} {response.text[:600]}"
    _assert_success_readback(client, booking_id, "accepted")


def _reject(client: ApiClient, booking_id: int, request) -> None:
    reason = _sample(request, BOOKING_ACTION, "reason[action=reject]", "valid:string")
    response = client.post(BOOKING_ACTION.format(booking_id=booking_id, action="reject"), json={"reason": reason})
    assert response.status_code == 200, f"setup reject failed: {response.status_code} {response.text[:600]}"
    _assert_success_readback(client, booking_id, "rejected")


def _cancel(client: ApiClient, booking_id: int) -> None:
    response = client.post(BOOKING_ACTION.format(booking_id=booking_id, action="cancel"))
    assert response.status_code == 200, f"setup cancel failed: {response.status_code} {response.text[:600]}"
    _assert_success_readback(client, booking_id, "cancelled")


def _set_accepted_booking_outside_cancel_grace(app_control, booking_id: int) -> None:
    app_control.call("outside_cancel_grace", booking_id=booking_id)


def _transition_params() -> list:
    """Select success and denial combinations from the generated business rules."""
    scenarios = [
        ("BR2", {"is_pending": True, "can_moderate": True}, "pending", "approve", "moderator", "accepted"),
        ("BR3_REJECT", {"is_terminal_state": False, "can_moderate": True, "reason_present": True},
         "pending", "reject", "moderator", "rejected"),
        ("BR3_REJECT", {"is_terminal_state": False, "can_moderate": True, "reason_present": True},
         "accepted", "reject", "moderator", "rejected"),
        ("BR3_CANCEL", {"state": "pending", "is_booker_or_booked_for": True,
                         "is_rb_admin": False, "within_cancel_grace_period": False},
         "pending", "cancel", "booker", "cancelled"),
        ("BR3_CANCEL", {"state": "accepted", "is_booker_or_booked_for": True,
                         "is_rb_admin": False, "within_cancel_grace_period": True},
         "accepted", "cancel", "booker", "cancelled"),
        ("BR2", {"is_pending": True, "can_moderate": False}, "pending", "approve", "booker", None),
        ("BR2", {"is_pending": False, "can_moderate": True}, "accepted", "approve", "moderator", None),
        ("BR3_CANCEL", {"state": "rejected", "is_booker_or_booked_for": True,
                         "is_rb_admin": False, "within_cancel_grace_period": False},
         "rejected", "cancel", "booker", None),
        ("BR2", {"is_pending": False, "can_moderate": True}, "cancelled", "approve", "moderator", None),
    ]
    params = []
    for rule, conditions, source_state, action, actor, target_state in scenarios:
        decision = next(
            item for item in _decision_cases(rule)
            if item["value"]["conditions"] == conditions
        )
        scenario = {
            "decision": decision,
            "source_state": source_state,
            "action": action,
            "actor": actor,
            "target_state": target_state,
        }
        params.append(pytest.param(scenario, id=f"{source_state}-to-{target_state or 'denied'}-{action}"))
    return params


@pytest.mark.parametrize("scenario", _transition_params())
def test_allowed_and_disallowed_state_transitions(scenario, request, user1, mgr1):
    """Every allowed transition is applied; each state also has a denied transition."""
    decision = scenario["decision"]
    booking = request.getfixturevalue("booking_id")
    source = scenario["source_state"]
    if source == "accepted":
        _approve(mgr1, booking)
    elif source == "rejected":
        _reject(mgr1, booking, request)
    elif source == "cancelled":
        _cancel(user1, booking)

    actor = mgr1 if scenario["actor"] == "moderator" else user1
    action = _sample(request, BOOKING_ACTION, "action", f"valid:enum={scenario['action']}")
    path = BOOKING_ACTION.format(booking_id=booking, action=action)
    before = _record_signature(read_back(user1, booking))
    if action == "reject":
        reason = _sample(request, BOOKING_ACTION, "reason[action=reject]", "valid:string")
        response = actor.post(path, json={"reason": reason})
    elif action == "approve":
        response = actor.post(path, json={})
    else:
        response = actor.post(path)

    if response.status_code >= 400 or scenario["target_state"] is None:
        _assert_unchanged(user1, booking, before)
    expected = decision["expected_status"]
    _assert_status(response, expected, _safe_request_description("POST", path, None), decision["id"])
    after = _record_signature(read_back(user1, booking))
    if scenario["target_state"] is not None:
        assert after["state"] == scenario["target_state"]
    else:
        assert after == before


def test_repeated_booking_requests_do_not_create_duplicates(request, user1):
    """The same generated request sent twice must leave only the first Reservation."""
    payload = _create_payload(request)
    first = user1.post(CREATE, json=payload)
    assert first.status_code == 200, f"initial create failed: {first.status_code} {first.text[:1000]}"
    first_id = first.json()["booking"]["id"]
    before = _assert_success_readback(user1, first_id, "pending", payload)

    second = user1.post(CREATE, json=payload)
    if second.status_code >= 400:
        _assert_unchanged(user1, first_id, before)
    else:
        second_id = second.json()["booking"]["id"]
        _assert_success_readback(user1, second_id, "pending", payload)
        assert second_id == first_id, (
            f"repeated request created a duplicate: first_id={first_id}, second_id={second_id}; "
            f"request={_safe_request_description('POST', CREATE, payload)}; "
            f"response_status={second.status_code}; response_booking_id={second_id}"
        )
    assert second.status_code != 200 or second.json()["booking"]["id"] == first_id


def test_rapid_concurrent_booking_requests_do_not_create_duplicates(
    request, user1, base_url, anchor_booking, client_for_token
):
    """Two concurrent identical generated requests may create at most one record."""
    payload = _create_payload(request)
    anchor_before = _record_signature(read_back(user1, anchor_booking))
    clients = [client_for_token(), client_for_token()]
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda client: client.post(CREATE, json=payload), clients))
        successes = [response for response in responses if response.status_code == 200]
        successful_records = [
            (response, response.json()["booking"]["id"])
            for response in successes
        ]
        signatures = {
            booking_id: _assert_success_readback(user1, booking_id, "pending", payload)
            for _, booking_id in successful_records
        }
        assert len(successes) == 1, (
            f"rapid duplicate request count: {len(successes)} HTTP 200 responses; "
            f"request={_safe_request_description('POST', CREATE, payload)}; "
            f"responses={[{'status': r.status_code, 'booking_id': (r.json().get('booking') or {}).get('id') if r.status_code == 200 else None} for r in responses]}"
        )
        for response in responses:
            if response.status_code >= 400:
                assert _error_body_is_shaped(response)
                _assert_unchanged(user1, anchor_booking, anchor_before)
                for booking_id, before in signatures.items():
                    _assert_unchanged(user1, booking_id, before)
    finally:
        for client in clients:
            client.session.close()


def test_workflow_b_reads_and_changes_workflow_a_record(request, user1, mgr1):
    """The moderator sees workflow A's pending record, approves it, and the booker reads accepted state."""
    payload = _create_payload(request)
    created = user1.post(CREATE, json=payload)
    assert created.status_code == 200, f"workflow A create failed: {created.status_code} {created.text[:900]}"
    booking_id = created.json()["booking"]["id"]
    _assert_success_readback(user1, booking_id, "pending", payload)

    manager_read = read_back(mgr1, booking_id)
    assert manager_read.status_code == 200
    assert manager_read.json()["state"] == "pending"

    approved = mgr1.post(BOOKING_ACTION.format(booking_id=booking_id, action="approve"), json={})
    assert approved.status_code == 200, f"workflow B approve failed: {approved.status_code} {approved.text[:900]}"
    assert _assert_success_readback(user1, booking_id, "accepted")["state"] == "accepted"


def test_lower_privileged_role_cannot_moderate(request, user1, mgr1):
    """The booker is denied approval and the pending shared record stays unchanged."""
    payload = _create_payload(request)
    created = user1.post(CREATE, json=payload)
    assert created.status_code == 200
    booking_id = created.json()["booking"]["id"]
    _assert_success_readback(user1, booking_id, "pending", payload)
    before = _record_signature(read_back(mgr1, booking_id))

    denied = user1.post(BOOKING_ACTION.format(booking_id=booking_id, action="approve"), json={})
    assert denied.status_code == 403, f"expected lower-role denial; got {denied.status_code}: {denied.text[:900]}"
    assert _error_body_is_shaped(denied)
    _assert_unchanged(mgr1, booking_id, before)


def test_lower_privileged_role_cannot_direct_book_confirmation_room(request, user1, room_id, anchor_booking):
    """The booker is denied direct booking in the seeded confirmation-required room."""
    payload = _create_payload(request)
    payload["is_prebooking"] = False
    before = _record_signature(read_back(user1, anchor_booking))
    response = user1.post(CREATE, json=payload)
    assert response.status_code == 403, f"expected direct-book denial; got {response.status_code}: {response.text[:900]}"
    assert _error_body_is_shaped(response)
    _assert_unchanged(user1, anchor_booking, before)
