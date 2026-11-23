"""Area 1 decision tests for reservation approval, rejection, and cancellation."""

from datetime import datetime, timedelta

import pytest

from indico.modules.rb.models.reservations import ReservationState


@pytest.mark.parametrize(('state', 'manager', 'expected'), (
    pytest.param(ReservationState.pending, True, True, id='BR2-row-01-pending-manager'),
    pytest.param(ReservationState.pending, False, False, id='BR2-row-02-pending-nonmanager'),
    pytest.param(ReservationState.accepted, True, False, id='BR2-row-03-accepted-manager'),
))
def test_br2_can_accept_decision_table(dummy_reservation, create_user, state, manager, expected):
    user = create_user(123)
    dummy_reservation.state = state
    if manager:
        dummy_reservation.room.update_principal(user, permissions={'moderate'})

    assert dummy_reservation.can_accept(user) is expected


@pytest.mark.parametrize(('state', 'manager', 'expected'), (
    pytest.param(ReservationState.pending, True, True, id='BR3-row-01-pending-manager'),
    pytest.param(ReservationState.pending, False, False, id='BR3-row-02-pending-nonmanager'),
    pytest.param(ReservationState.rejected, True, False, id='BR3-row-03-rejected-manager'),
    pytest.param(ReservationState.cancelled, True, False, id='BR3-row-04-cancelled-manager'),
))
def test_br3_can_reject_decision_table(dummy_reservation, create_user, state, manager, expected):
    user = create_user(123)
    dummy_reservation.state = state
    if manager:
        dummy_reservation.room.update_principal(user, permissions={'moderate'})

    assert dummy_reservation.can_reject(user) is expected


@pytest.mark.parametrize(('state', 'actor', 'when', 'is_admin', 'allow_admin', 'expected'), (
    pytest.param(ReservationState.pending, 'owner', 1, False, True, True,
                 id='BR3-row-01-pending-owner'),
    pytest.param(ReservationState.accepted, 'owner', 1, False, True, True,
                 id='BR3-row-02-future-owner'),
    pytest.param(ReservationState.accepted, 'owner', -2, False, True, False,
                 id='BR3-row-03-past-outside-grace'),
    pytest.param(ReservationState.accepted, 'stranger', 1, False, True, False,
                 id='BR3-row-04-stranger'),
    pytest.param(ReservationState.accepted, 'admin', 1, True, True, True,
                 id='BR3-row-05-admin-allowed'),
    pytest.param(ReservationState.accepted, 'admin', 1, True, False, False,
                 id='BR3-row-06-admin-disabled'),
    pytest.param(ReservationState.rejected, 'owner', 1, False, True, False,
                 id='BR3-row-07-rejected'),
    pytest.param(ReservationState.cancelled, 'owner', 1, False, True, False,
                 id='BR3-row-08-cancelled'),
))
def test_br3_can_cancel_decision_table(create_reservation, create_user, state, actor, when, is_admin,
                                      allow_admin, expected):
    owner = create_user(124)
    admin = create_user(125, rb_admin=is_admin)
    stranger = create_user(126)
    user = {'owner': owner, 'admin': admin, 'stranger': stranger}[actor]
    start = datetime.combine(datetime.today().date() + timedelta(days=when), datetime.min.time())
    reservation = create_reservation(state=state, start_dt=start, end_dt=start)
    reservation.created_by_user = owner

    assert reservation.can_cancel(user, allow_admin=allow_admin) is expected


def test_br3_can_cancel_requires_a_user(dummy_reservation):
    assert dummy_reservation.can_cancel(None) is False


def test_br3_can_cancel_rejects_archived_reservation(create_reservation, create_user):
    owner = create_user(127)
    start = datetime.combine(datetime.today().date() - timedelta(days=10), datetime.min.time())
    reservation = create_reservation(state=ReservationState.accepted, start_dt=start, end_dt=start)
    reservation.created_by_user = owner
    assert reservation.is_archived
    assert reservation.can_cancel(owner) is False


def test_br2_can_accept_requires_a_user(dummy_reservation):
    assert dummy_reservation.can_accept(None) is False


def test_br3_can_reject_requires_a_user(dummy_reservation):
    assert dummy_reservation.can_reject(None) is False


class _OccurrenceQuery:
    def __init__(self):
        self.filter_args = None
        self.updated = None

    def filter(self, *args):
        self.filter_args = args
        return self

    def filter_by(self, **kwargs):
        self.filter_args = kwargs
        return self

    def update(self, values, **kwargs):
        self.updated = (values, kwargs)


class _StateChangeReservation:
    def __init__(self, pending=True):
        self.is_pending = pending
        self.occurrences = _OccurrenceQuery()
        self.edit_logs = []
        self.state = None
        self.rejection_reason = None

    def add_edit_log(self, edit_log):
        self.edit_logs.append(edit_log)


@pytest.mark.parametrize(('reason', 'expected_log'), (
    pytest.param('Approved', 'Reservation accepted: Approved', id='BR3-accept-with-reason'),
    pytest.param(None, 'Reservation accepted', id='BR3-accept-no-reason'),
))
def test_br3_accept_state_change(monkeypatch, reason, expected_log):
    import indico.modules.rb.models.reservations as rb_reservations
    from indico.modules.rb.models.reservations import Reservation, ReservationState

    actor = type('Actor', (), {'full_name': 'Moderator'})()
    booking = _StateChangeReservation()
    rejected = []
    monkeypatch.setattr(rb_reservations, 'notify_confirmation', lambda *_: None)
    monkeypatch.setattr(rb_reservations, 'get_prebooking_collisions', lambda _: [
        type('Collision', (), {'reject': lambda self, user, why: rejected.append((user, why))})()
    ] if reason == 'Approved' else [])

    Reservation.accept(booking, actor, reason)

    assert booking.state == ReservationState.accepted
    assert booking.edit_logs[0].info == [expected_log]
    assert len(rejected) == (1 if reason else 0)


@pytest.mark.parametrize(('silent', 'reason'), (
    pytest.param(False, 'No longer available', id='BR3-reject-notify'),
    pytest.param(True, '', id='BR3-reject-silent-empty-reason'),
))
def test_br3_reject_state_change(monkeypatch, silent, reason):
    import indico.modules.rb.models.reservations as rb_reservations
    from indico.modules.rb.models.reservations import Reservation, ReservationState

    actor = type('Actor', (), {'full_name': 'Moderator'})()
    booking = _StateChangeReservation()
    notifications = []
    monkeypatch.setattr(rb_reservations, 'notify_rejection', lambda *_: notifications.append(True))

    Reservation.reject(booking, actor, reason, silent=silent)

    assert booking.state == ReservationState.rejected
    assert booking.rejection_reason == (reason or None)
    assert booking.occurrences.updated[0][rb_reservations.ReservationOccurrence.rejection_reason] == reason
    assert bool(notifications) is (not silent)
    assert bool(booking.edit_logs) is (not silent)


@pytest.mark.parametrize(('pending', 'reason', 'silent', 'notify'), (
    pytest.param(True, None, False, True, id='BR3-cancel-pending-notify'),
    pytest.param(False, 'Changed plans', False, True, id='BR3-cancel-accepted-reason'),
    pytest.param(False, None, True, False, id='BR3-cancel-accepted-silent'),
))
def test_br3_cancel_state_change(monkeypatch, pending, reason, silent, notify):
    import indico.modules.rb.models.reservations as rb_reservations
    from indico.modules.rb.models.reservations import Reservation, ReservationState

    actor = type('Actor', (), {'full_name': 'Booker'})()
    booking = _StateChangeReservation(pending=pending)
    notifications = []
    monkeypatch.setattr(rb_reservations, 'notify_cancellation', lambda *_: notifications.append(True))

    Reservation.cancel(booking, actor, reason, silent=silent)

    assert booking.state == ReservationState.cancelled
    assert booking.rejection_reason == reason
    assert bool(notifications) is notify
    assert bool(booking.edit_logs) is notify
    assert len(booking.occurrences.filter_args) == (1 if pending else 2)
