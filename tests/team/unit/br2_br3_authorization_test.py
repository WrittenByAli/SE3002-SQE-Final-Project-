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
