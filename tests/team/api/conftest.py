"""Pytest fixtures for Fahima's Room Booking API tests.

Each test module begins with the documented reset-and-seed command. API input values
are selected from tools/testgen/out/cases.json; fixture markers are resolved here.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
import requests


REPO_ROOT = Path(__file__).resolve().parents[3]
CASE_FILE = REPO_ROOT / "tools" / "testgen" / "out" / "cases.json"
SEED_ENV_FILE = REPO_ROOT / "tests" / "team" / ".env.test"
RESET_SCRIPT = REPO_ROOT / "tests" / "team" / "seed" / "reset.sh"
APP_COMPOSE_DIR = REPO_ROOT / "infra" / "indico-containers" / "indico-prod"
MISSING = object()


def _read_seed_environment() -> dict[str, str]:
    """Read the ignored env file written by the reset-and-seed script."""
    if not SEED_ENV_FILE.exists():
        raise RuntimeError(
            f"{SEED_ENV_FILE} was not created by the documented reset-and-seed command"
        )

    values = {}
    for line in SEED_ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _bash_executable() -> str:
    """Find the shell used by the reset command in setup.md."""
    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        git_bash = Path(program_files) / "Git" / "bin" / "bash.exe"
        if git_bash.exists():
            return str(git_bash)

    bash = shutil.which("bash")
    if bash:
        return bash
    raise FileNotFoundError("bash is required to run tests/team/seed/reset.sh")


@pytest.fixture(scope="module", autouse=True)
def reset_and_seed() -> dict[str, str]:
    """Run the setup guide's reset-and-reseed command once before each test module.

    The script drops the local Compose database, Redis, and file volumes, then starts
    the stack and rewrites the ignored tests/team/.env.test with fresh test tokens.
    Build the images once using the prerequisite commands in docs/api/setup.md.
    """
    subprocess.run(
        [_bash_executable(), str(RESET_SCRIPT)],
        cwd=REPO_ROOT,
        check=True,
        timeout=900,
    )
    settings = _read_seed_environment()
    base_url = os.environ.get("INDICO_BASE_URL") or settings.get("INDICO_BASE_URL")
    if not base_url:
        raise RuntimeError("Set INDICO_BASE_URL or run the documented reset-and-seed command")
    os.environ.setdefault("INDICO_BASE_URL", base_url)
    settings["INDICO_BASE_URL"] = os.environ["INDICO_BASE_URL"].rstrip("/")

    required = ("ROOM_ID", "USER1_TOKEN", "MGR1_TOKEN")
    missing = [name for name in required if not settings.get(name)]
    if missing:
        raise RuntimeError(f"The reset script did not write required settings: {', '.join(missing)}")
    return settings


@pytest.fixture(scope="module")
def base_url(reset_and_seed: dict[str, str]) -> str:
    """The Indico root URL, taken from the INDICO_BASE_URL environment variable."""
    return os.environ["INDICO_BASE_URL"].rstrip("/")


@pytest.fixture(scope="module")
def room_id(reset_and_seed: dict[str, str]) -> int:
    return int(reset_and_seed["ROOM_ID"])


class ApiClient:
    """A requests.Session wrapper that accepts API paths and returns raw responses."""

    def __init__(self, session: requests.Session, base_url: str):
        self.session = session
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        path = path.lstrip("/")
        if path.startswith("rooms/api/"):
            return f"{self.base_url}/{path}"
        return f"{self.base_url}/rooms/api/{path}"

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", 30)
        return self.session.request(method, self._url(path), **kwargs)

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, json=None, **kwargs) -> requests.Response:
        return self.request("POST", path, json=json, **kwargs)


def _make_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
        }
    )
    return session


@pytest.fixture(scope="module")
def user1_session(reset_and_seed: dict[str, str]) -> requests.Session:
    session = _make_session(reset_and_seed["USER1_TOKEN"])
    # Match the valid value generated for the JSON error-representation header.
    xhr_value = next(
        case["value"]
        for case in load_cases(field="X-Requested-With", technique="EP", expected_valid=True)
        if not isinstance(case["value"], dict)
    )
    session.headers["X-Requested-With"] = xhr_value
    yield session
    session.close()


@pytest.fixture(scope="module")
def mgr1_session(reset_and_seed: dict[str, str]) -> requests.Session:
    session = _make_session(reset_and_seed["MGR1_TOKEN"])
    xhr_value = next(
        case["value"]
        for case in load_cases(field="X-Requested-With", technique="EP", expected_valid=True)
        if not isinstance(case["value"], dict)
    )
    session.headers["X-Requested-With"] = xhr_value
    yield session
    session.close()


@pytest.fixture(scope="module")
def user1(user1_session: requests.Session, base_url: str) -> ApiClient:
    return ApiClient(user1_session, base_url)


@pytest.fixture(scope="module")
def mgr1(mgr1_session: requests.Session, base_url: str) -> ApiClient:
    return ApiClient(mgr1_session, base_url)


@pytest.fixture(scope="module")
def client_for_token(base_url: str, reset_and_seed: dict[str, str]):
    """Create an independent API session for a token, useful for concurrent requests."""
    sessions: list[requests.Session] = []

    def make_client(token: str | None = None) -> ApiClient:
        token = token or reset_and_seed["USER1_TOKEN"]
        session = _make_session(token)
        xhr_value = next(
            case["value"]
            for case in load_cases(field="X-Requested-With", technique="EP", expected_valid=True)
            if case["value"] is not None and not isinstance(case["value"], dict)
        )
        session.headers["X-Requested-With"] = xhr_value
        sessions.append(session)
        return ApiClient(session, base_url)

    yield make_client
    for session in sessions:
        session.close()


@pytest.fixture(scope="module")
def booker(user1: ApiClient) -> ApiClient:
    return user1


@pytest.fixture(scope="module")
def moderator(mgr1: ApiClient) -> ApiClient:
    return mgr1


def read_back(client: ApiClient, booking_id: int | str) -> requests.Response:
    """Fetch the shared Reservation record through the booking detail API."""
    return client.get(f"/bookings/{booking_id}")


class IndicoAppControl:
    """Keep one app context alive for small DB setup/read commands during a test module."""

    SCRIPT = r"""
import json, sys
from indico.web.flask.app import make_app
app = make_app()
context = app.app_context()
context.push()
from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.oauth.models.personal_tokens import PersonalToken
from indico.modules.auth.models.identities import Identity
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
print(json.dumps({'ready': True}), flush=True)
for line in sys.stdin:
    try:
        command = json.loads(line)
        operation = command['operation']
        if operation == 'room':
            room = Room.get(command['room_id'])
            user = Identity.query.filter_by(provider='indico', identifier='user1').one().user
            room.is_reservable = command['reservable']
            room.protection_mode = ProtectionMode.public if command['public'] else ProtectionMode.protected
            room.reservations_need_confirmation = command['confirmation']
            permission = command.get('permission')
            permissions = {permission} if permission else set()
            room.update_principal(user, permissions=permissions, read_access=False,
                                  full_access=False, quiet=True)
            db.session.commit()
            result = {'ok': True}
        elif operation == 'user_identifier':
            user = Identity.query.filter_by(provider='indico', identifier='user1').one().user
            result = {'ok': True, 'value': user.identifier}
        elif operation == 'admin_token':
            user = Identity.query.filter_by(provider='indico', identifier='admin').one().user
            token = PersonalToken(user=user, name='sqe-api-tests-admin', scopes={'full:everything'})
            db.session.add(token)
            value = token.generate_token()
            db.session.commit()
            result = {'ok': True, 'value': value}
        elif operation == 'outside_cancel_grace':
            booking = Reservation.get(command['booking_id'])
            occurrence = booking.occurrences.first()
            from datetime import datetime, timedelta
            start = datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=20)
            end = start + timedelta(hours=1)
            occurrence.start_dt = start
            occurrence.end_dt = end
            booking.start_dt = start
            booking.end_dt = end
            db.session.commit()
            result = {'ok': True}
        elif operation == 'exit':
            print(json.dumps({'ok': True}), flush=True)
            break
        else:
            raise ValueError(f'Unknown operation: {operation}')
        db.session.remove()
        print(json.dumps(result), flush=True)
    except Exception as error:
        db.session.rollback()
        db.session.remove()
        print(json.dumps({'ok': False, 'error': f'{type(error).__name__}: {error}'}), flush=True)
context.pop()
"""

    def __init__(self):
        command = [
            "docker", "compose", "exec", "-T", "indico-web",
            "/opt/indico/.venv/bin/python", "-u", "-c", self.SCRIPT,
        ]
        self.process = subprocess.Popen(
            command,
            cwd=APP_COMPOSE_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        ready = self.process.stdout.readline()
        try:
            response = json.loads(ready)
        except json.JSONDecodeError as error:
            stderr = self.process.stderr.read() if self.process.poll() is not None else ""
            raise RuntimeError(f"Indico app control did not start: {ready!r} {stderr}") from error
        if response != {"ready": True}:
            raise RuntimeError(f"Unexpected Indico app-control startup response: {response}")

    def call(self, operation: str, **values):
        command = {"operation": operation, **values}
        self.process.stdin.write(json.dumps(command) + "\n")
        self.process.stdin.flush()
        response = json.loads(self.process.stdout.readline())
        if not response.get("ok"):
            raise RuntimeError(f"Indico app-control command failed: {response.get('error')}")
        return response.get("value")

    def close(self):
        if self.process.poll() is None:
            try:
                self.call("exit")
                self.process.wait(timeout=60)
            except Exception:
                self.process.terminate()
                self.process.wait(timeout=10)
        if self.process.stderr:
            self.process.stderr.close()


@pytest.fixture(scope="module")
def app_control(reset_and_seed: dict[str, str]):
    control = IndicoAppControl()
    yield control
    control.close()


def load_cases(
    endpoint: str | None = None,
    method: str | None = None,
    field: str | None = None,
    technique: str | None = None,
    expected_valid: bool | None = None,
) -> list[dict]:
    """Load generated API cases and apply optional endpoint/technique filters."""
    if not CASE_FILE.exists():
        raise FileNotFoundError(f"{CASE_FILE} is missing; run python tools/testgen/generate.py")

    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    selected = []
    for case in cases:
        if endpoint is not None and case["endpoint"] != endpoint:
            continue
        if method is not None and case["method"] != method.upper():
            continue
        if field is not None and case["field"] != field:
            continue
        if technique is not None and case["technique"] != technique:
            continue
        if expected_valid is not None and case["expected_valid"] is not expected_valid:
            continue
        selected.append(case)
    return selected


def case_params(**filters) -> list:
    """Return pytest parameters whose displayed test IDs are the generated case IDs."""
    return [pytest.param(case, id=case["id"]) for case in load_cases(**filters)]


def case_value(case: dict, request: pytest.FixtureRequest):
    """Resolve the case value, including fixture markers and the missing-field marker."""
    return _resolve_value(case["value"], request)


def _resolve_value(value, request: pytest.FixtureRequest):
    if isinstance(value, dict) and value == {"$missing": True}:
        return MISSING
    if isinstance(value, dict) and set(value) == {"$fixture"}:
        names = value["$fixture"].split(".")
        resolved = request.getfixturevalue(names[0])
        for name in names[1:]:
            resolved = getattr(resolved, name)
        return resolved
    if isinstance(value, dict):
        return {key: _resolve_value(item, request) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_value(item, request) for item in value]
    return value


@dataclass(frozen=True)
class FreeSlot:
    """Dynamically chosen slot used only to resolve generator fixture markers."""

    start: datetime
    end: datetime

    @property
    def start_rfc3339(self) -> str:
        return self.start.isoformat(timespec="seconds")

    @property
    def end_rfc3339(self) -> str:
        return self.end.isoformat(timespec="seconds")

    def __iter__(self):
        yield self.start
        yield self.end


SLOTS_PER_DAY = 12
_slot_counter = iter(range(random.SystemRandom().randrange(0, 200_000), 10**9))


@pytest.fixture
def free_slot() -> FreeSlot:
    """Provide fresh timestamps for the generated free_slot.start/end markers."""
    slot_number = next(_slot_counter)
    day = date.today() + timedelta(days=30 + slot_number // SLOTS_PER_DAY)
    start = datetime.combine(day, datetime.min.time()).replace(hour=8 + slot_number % SLOTS_PER_DAY)
    return FreeSlot(start, start + timedelta(hours=1))
