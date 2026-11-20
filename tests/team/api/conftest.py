"""Shared fixtures for API/integration tests (Area 2: Fahima).

Reads tests/team/.env.test (written by tests/team/seed/reset.sh) for the base URL, room id and Bearer tokens.
Each test should create the data it needs; run `bash tests/team/run.sh env-reset` before a full suite run.
"""
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
import requests

ENV_FILE = Path(__file__).resolve().parents[1] / '.env.test'


def _load_env():
    if not ENV_FILE.exists():
        pytest.exit(f'{ENV_FILE} missing: run `bash tests/team/run.sh env-reset` first', returncode=2)
    pairs = (line.split('=', 1) for line in ENV_FILE.read_text().splitlines() if '=' in line)
    return {k.strip(): v.strip() for k, v in pairs}


ENV = _load_env()
BASE = ENV['INDICO_BASE_URL'].rstrip('/') + '/rooms/api'


class Api:
    """Tiny client: every call returns the raw `requests.Response` so tests assert status AND body."""

    def __init__(self, token):
        self.s = requests.Session()
        self.s.headers.update({'Authorization': f'Bearer {token}', 'Accept': 'application/json'})

    def post(self, path, json=None):
        return self.s.post(BASE + path, json=json if json is not None else {}, timeout=30)

    def get(self, path):
        return self.s.get(BASE + path, timeout=30)


@pytest.fixture(scope='session')
def room_id():
    return int(ENV['ROOM_ID'])


@pytest.fixture(scope='session')
def user1():
    return Api(ENV['USER1_TOKEN'])


@pytest.fixture(scope='session')
def mgr1():
    return Api(ENV['MGR1_TOKEN'])


# Each run starts at a random slot so repeated runs WITHOUT env-reset never collide with bookings approved earlier
# (a collision shows up as 418 "Reservation has no valid occurrences"). 12 one-hour slots per day (08:00-19:00),
# ~45 years of future days -> ~200k slots; a run uses a few hundred. The test VALUES stay deterministic, only the slot moves.
SLOTS_PER_DAY = 12
_slot_counter = iter(range(random.SystemRandom().randrange(0, 200_000), 10**9))


@pytest.fixture
def free_slot():
    """A future 1-hour slot that no other test (in this or an earlier run) uses."""
    n = next(_slot_counter)
    day = date.today() + timedelta(days=30 + n // SLOTS_PER_DAY)
    start = datetime.combine(day, datetime.min.time()).replace(hour=8 + n % SLOTS_PER_DAY)
    return start, start + timedelta(hours=1)


def booking_payload(room_id, start, end, **overrides):
    body = {
        'room_id': room_id,
        'start_dt': start.strftime('%Y-%m-%dT%H:%M:%S'),
        'end_dt': end.strftime('%Y-%m-%dT%H:%M:%S'),
        'repeat_frequency': 'NEVER',
        'repeat_interval': 0,
        'reason': 'SQE API test',
        'is_prebooking': True,
    }
    body.update(overrides)
    return body
