"""Focused MCC/MC-DC tests for the Boolean decisions in Reservation.can_cancel."""

import pytest

import indico.modules.rb.models.reservations as reservations_module
from indico.modules.rb.models.reservations import Reservation


class _Occurrences:
    def __init__(self, has_grace_occurrence):
        self.has_grace_occurrence = has_grace_occurrence

    def filter(self, _criterion):
        return self

    def has_rows(self):
        return self.has_grace_occurrence


class _Reservation:
    """Small decision fixture; the production method under test is unchanged."""

    def __init__(self, *, rejected=False, cancelled=False, archived=False, pending=True,
                 has_grace_occurrence=True, owner=False, booked_for=False):
        self.is_rejected = rejected
        self.is_cancelled = cancelled
        self.is_archived = archived
        self.is_pending = pending
        self.occurrences = _Occurrences(has_grace_occurrence)
        self._owner = owner
        self._booked_for = booked_for

    def is_owned_by(self, _user):
        return self._owner

    def is_booked_for(self, _user):
        return self._booked_for


@pytest.mark.parametrize(('rejected', 'cancelled', 'archived', 'expected'), (
    pytest.param(False, False, False, True, id='mcc-state-000-active'),
    pytest.param(True, False, False, False, id='mcc-state-100-rejected'),
    pytest.param(False, True, False, False, id='mcc-state-010-cancelled'),
    pytest.param(False, False, True, False, id='mcc-state-001-archived'),
    pytest.param(True, False, True, False, id='mcc-state-101-rejected-archived'),
    pytest.param(False, True, True, False, id='mcc-state-011-cancelled-archived'),
))
def test_can_cancel_mcc_state_guard(rejected, cancelled, archived, expected):
    # Rejected and cancelled are mutually exclusive ReservationState values.
    reservation = _Reservation(rejected=rejected, cancelled=cancelled, archived=archived, owner=True)

    assert Reservation.can_cancel(reservation, object()) is expected


@pytest.mark.parametrize(('pending', 'has_grace_occurrence', 'expected'), (
    pytest.param(True, True, True, id='mcc-grace-00-pending-within-grace'),
    pytest.param(True, False, True, id='mcc-grace-01-pending-outside-grace'),
    pytest.param(False, True, True, id='mcc-grace-10-accepted-within-grace'),
    pytest.param(False, False, False, id='mcc-grace-11-accepted-outside-grace'),
))
def test_can_cancel_mcc_pending_and_grace(pending, has_grace_occurrence, expected):
    reservation = _Reservation(pending=pending, has_grace_occurrence=has_grace_occurrence, owner=True)

    assert Reservation.can_cancel(reservation, object()) is expected


@pytest.mark.parametrize(('owner', 'booked_for', 'allow_admin', 'admin', 'expected'), [
    pytest.param(bool(owner), bool(booked_for), bool(allow_admin), bool(admin),
                 bool(owner or booked_for or (allow_admin and admin)),
                 id=f'mcc-final-{owner}{booked_for}{allow_admin}{admin}')
    for owner in (0, 1)
    for booked_for in (0, 1)
    for allow_admin in (0, 1)
    for admin in (0, 1)
])
def test_can_cancel_mcc_authorization(owner, booked_for, allow_admin, admin, expected, monkeypatch):
    user = object()
    monkeypatch.setattr(reservations_module, 'rb_is_admin', lambda candidate: candidate is user and admin)
    reservation = _Reservation(owner=owner, booked_for=booked_for)

    assert Reservation.can_cancel(reservation, user, allow_admin=allow_admin) is expected


def test_can_cancel_rejects_missing_user_before_other_conditions():
    reservation = _Reservation(owner=True)

    assert Reservation.can_cancel(reservation, None) is False
