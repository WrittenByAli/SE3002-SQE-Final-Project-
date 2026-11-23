"""Area 1 decision tests for booking date limits and room booking permissions."""

from datetime import datetime, timedelta

import pytest
import pytz

from indico.core.db.sqlalchemy.util.models import import_all_models

import_all_models()

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.config import config
from indico.modules.rb import rb_settings, util as rb_util
from indico.modules.rb.controllers.backend.bookings import RHCreateBooking


@pytest.mark.parametrize(('start', 'end', 'limit', 'expected'), (
    pytest.param(datetime(2026, 12, 1, 8), datetime(2026, 12, 1, 9), 0, True,
                 id='BR1-row-01-same-day-at-zero-limit'),
    pytest.param(datetime(2026, 12, 1, 8), datetime(2026, 12, 2, 9), 1, True,
                 id='BR1-row-02-next-day-at-limit'),
    pytest.param(datetime(2026, 12, 1, 8), datetime(2026, 12, 3, 9), 1, False,
                 id='BR1-row-03-over-limit'),
))
def test_br1_booking_length_boundary(start, end, limit, expected):
    assert RHCreateBooking._validate_room_booking_limit(None, start, end, limit) is expected


def test_br1_grace_period_accepts_exact_boundary(monkeypatch, freeze_time):
    start = datetime(2026, 12, 1, 10)
    timezone = pytz.timezone(config.DEFAULT_TIMEZONE)
    now = timezone.localize(start).astimezone(pytz.utc) + timedelta(hours=2)
    freeze_time(now)
    monkeypatch.setattr(rb_settings, 'get', lambda key: 2)

    assert rb_util.is_booking_start_within_grace_period(start, user=object()) is True


def test_br1_grace_period_rejects_start_before_boundary(monkeypatch, freeze_time):
    start = datetime(2026, 12, 1, 9, 59)
    timezone = pytz.timezone(config.DEFAULT_TIMEZONE)
    now = timezone.localize(datetime(2026, 12, 1, 10)).astimezone(pytz.utc) + timedelta(hours=2)
    freeze_time(now)
    monkeypatch.setattr(rb_settings, 'get', lambda key: 2)

    assert rb_util.is_booking_start_within_grace_period(start, user=object()) is False


@pytest.mark.parametrize(('needs_confirmation', 'book', 'prebook'), (
    pytest.param(False, True, False, id='BR4-row-01-public-auto-confirm'),
    pytest.param(True, False, True, id='BR4-row-02-public-confirmation'),
))
def test_br4_public_room_booking_modes(dummy_room, create_user, needs_confirmation, book, prebook):
    dummy_room.protection_mode = ProtectionMode.public
    dummy_room.reservations_need_confirmation = needs_confirmation
    user = create_user(123)

    assert dummy_room.can_book(user) is book
    assert dummy_room.can_prebook(user) is prebook


def test_br4_room_booking_requires_user(dummy_room):
    assert dummy_room.can_book(None) is False
    assert dummy_room.can_prebook(None) is False


def test_br1_grace_period_with_no_limit_uses_server_local_date(monkeypatch, freeze_time):
    start = datetime(2026, 12, 1, 10)
    timezone = pytz.timezone(config.DEFAULT_TIMEZONE)
    frozen_now = timezone.localize(datetime(2026, 12, 1, 9)).astimezone(pytz.utc)
    freeze_time(frozen_now)
    monkeypatch.setattr(rb_settings, 'get', lambda key: None)

    assert rb_util.is_booking_start_within_grace_period(start, user=object()) is True
    assert rb_util.is_booking_start_within_grace_period(datetime(2026, 11, 30, 23, 59), user=object()) is False


def test_br1_admin_override_bypasses_start_grace_period(monkeypatch):
    monkeypatch.setattr(rb_util, 'rb_is_admin', lambda user: user == 'admin')

    assert rb_util.is_booking_start_within_grace_period(datetime(2000, 1, 1), 'admin', allow_admin=True) is True


@pytest.mark.parametrize(('method', 'allow_admin'), (
    pytest.param('can_book', True, id='BR4-direct-nonreservable-denied'),
    pytest.param('can_prebook', True, id='BR4-prebook-nonreservable-denied'),
    pytest.param('can_book', False, id='BR4-direct-admin-override-disabled'),
    pytest.param('can_prebook', False, id='BR4-prebook-admin-override-disabled'),
))
def test_br4_nonreservable_room_denies_regular_user(dummy_room, create_user, method, allow_admin):
    dummy_room.is_reservable = False
    user = create_user(129, rb_admin=(allow_admin is False))

    assert getattr(dummy_room, method)(user, allow_admin=allow_admin) is False
