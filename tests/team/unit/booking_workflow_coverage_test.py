"""Focused branch tests for the BR1/BR3 booking request handlers."""

from contextlib import nullcontext
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from indico.core.errors import NoReportError
from indico.core.db.sqlalchemy.util.models import import_all_models

import_all_models()

from indico.modules.rb.controllers.backend import bookings as backend
from indico.modules.rb.controllers.backend.bookings import RHBookingStateActions, RHCreateBooking
from indico.modules.rb.models.reservations import ReservationState


class _OccurrenceList(list):
    def all(self):
        return self


def _create_handler(monkeypatch, *, start_ok=True, limit=5, create_error=None, link=None):
    handler = object.__new__(RHCreateBooking)
    room = SimpleNamespace(id=44, name='Room 44', booking_limit_days=limit)
    handler.room = room
    handler.prebook = True
    actor = object()
    handler.args = {
        'start_dt': datetime(2026, 12, 1, 9), 'end_dt': datetime(2026, 12, 1, 10),
        'admin_override_enabled': False, 'link_type': None, 'link_id': None, 'link_back': False,
    }
    monkeypatch.setattr(backend, 'session', SimpleNamespace(user=actor))
    monkeypatch.setattr(backend, 'is_booking_start_within_grace_period', lambda *a: start_ok)
    monkeypatch.setattr(backend, 'rb_settings', SimpleNamespace(get=lambda key: 5))
    monkeypatch.setattr(backend, 'track_location_changes', lambda: nullcontext())
    monkeypatch.setattr(backend.db.session, 'flush', lambda: None)
    monkeypatch.setattr(backend.db.session, 'rollback', lambda: None)
    monkeypatch.setattr(backend, 'serialize_occurrences', lambda occurrences, schema=None: ['serialized'])
    monkeypatch.setattr(backend, 'group_by_occurrence_date', lambda occurrences: occurrences)
    monkeypatch.setattr(backend, 'reservation_details_schema', SimpleNamespace(dump=lambda obj: {'id': 9}))
    monkeypatch.setattr(backend, 'jsonify', lambda **data: data)
    if create_error is not None:
        def create(*args, **kwargs):
            raise create_error
        monkeypatch.setattr(backend.Reservation, 'create_from_data', create)
    else:
        occurrence_query = _OccurrenceList([SimpleNamespace(linked_object=None)])
        reservation = SimpleNamespace(occurrences=occurrence_query)
        monkeypatch.setattr(backend.Reservation, 'create_from_data', lambda *a, **kw: reservation)
    if link is not None:
        handler.args.update(link_type='event', link_id=1, link_back=(link is True))
        linked = SimpleNamespace(event=SimpleNamespace(can_manage=lambda user: link != 'denied'),
                                 inherit_location=True, room=None)
        monkeypatch.setattr(backend, 'get_linked_object', lambda *a: None if link == 'missing' else linked)
    return handler


def test_br1_create_handler_rejects_start_outside_grace(monkeypatch):
    handler = _create_handler(monkeypatch, start_ok=False)
    with pytest.raises(Exception, match='starts in the past'):
        handler._process()


def test_br1_create_handler_rejects_booking_over_limit(monkeypatch):
    handler = _create_handler(monkeypatch, limit=1)
    handler.args['end_dt'] = datetime(2026, 12, 3, 10)
    with pytest.raises(Exception, match='may not be longer'):
        handler._process()


def test_br1_create_handler_uses_global_limit_when_room_has_none(monkeypatch):
    handler = _create_handler(monkeypatch, limit=None)
    handler.args['end_dt'] = datetime(2026, 12, 2, 10)
    result = handler._process()
    assert result['room_id'] == 44


def test_br1_create_handler_rolls_back_expected_domain_error(monkeypatch):
    handler = _create_handler(monkeypatch, create_error=NoReportError('conflict'))
    rolled_back = []
    monkeypatch.setattr(backend.db.session, 'rollback', lambda: rolled_back.append(True))
    with pytest.raises(Exception, match='conflict'):
        handler._process()
    assert rolled_back == [True]


@pytest.mark.parametrize(('prebook', 'link', 'expected_key'), (
    (True, None, 'pre_bookings'), (False, None, 'bookings'),
    (True, 'missing', 'pre_bookings'), (False, 'denied', 'bookings'),
    (False, True, 'bookings'), (False, 'no-backlink', 'bookings'),
))
def test_br1_create_handler_serializes_mode_and_optional_links(monkeypatch, prebook, link, expected_key):
    handler = _create_handler(monkeypatch, link=link)
    handler.prebook = prebook
    result = handler._process()
    assert expected_key in result['calendar_data']


@pytest.mark.parametrize(('prebook', 'allowed'), ((True, False), (False, False), (True, True), (False, True)))
def test_br4_create_access_uses_matching_room_permission(monkeypatch, prebook, allowed):
    handler = object.__new__(RHCreateBooking)
    handler.prebook = prebook
    actor = object()
    handler.room = SimpleNamespace(can_prebook=lambda user: allowed, can_book=lambda user: allowed)
    monkeypatch.setattr(backend, 'session', SimpleNamespace(user=actor))
    monkeypatch.setattr(backend.RHRoomBookingBase, '_check_access', lambda self: None)
    if allowed:
        handler._check_access()
    else:
        with pytest.raises(Exception):
            handler._check_access()


def _action_handler(action, booking):
    handler = object.__new__(RHBookingStateActions)
    handler.action = action
    handler.booking = booking
    return handler


@pytest.mark.parametrize(('action', 'pending', 'rejected', 'cancelled', 'permission', 'fails'), (
    ('approve', True, False, False, True, False), ('approve', False, False, False, True, True),
    ('reject', True, False, False, True, False), ('reject', True, True, False, True, True),
    ('cancel', True, False, False, True, False), ('cancel', True, False, True, True, True),
    ('bogus', True, False, False, True, True), ('reject', True, False, False, False, True),
))
def test_br3_state_action_access_guard(monkeypatch, action, pending, rejected, cancelled, permission, fails):
    booking = SimpleNamespace(is_pending=pending, is_rejected=rejected, is_cancelled=cancelled,
                              can_accept=lambda user: permission, can_reject=lambda user: permission,
                              can_cancel=lambda user: permission)
    handler = _action_handler(action, booking)
    monkeypatch.setattr(backend.RHBookingBase, '_check_access', lambda self: None)
    monkeypatch.setattr(backend, 'session', SimpleNamespace(user=object()))
    if fails:
        with pytest.raises(Exception):
            handler._check_access()
    else:
        handler._check_access()


@pytest.mark.parametrize('action', ('approve', 'reject', 'cancel', 'unknown', 'aardvark', 'booking'))
def test_br3_state_action_dispatch(monkeypatch, action):
    calls = []
    booking = SimpleNamespace(cancel=lambda user: calls.append('cancel'))
    handler = _action_handler(action, booking)
    handler.accept = lambda: calls.append('approve')
    handler.reject = lambda: calls.append('reject')
    monkeypatch.setattr(backend, 'session', SimpleNamespace(user=object()))
    monkeypatch.setattr(backend, 'serialize_booking_details', lambda value: {'ok': True})
    monkeypatch.setattr(backend, 'jsonify', lambda **data: data)
    assert handler._process() == {'booking': {'ok': True}}
    expected = {'approve': 'approve', 'reject': 'reject', 'cancel': 'cancel'}.get(action)
    assert calls == ([expected] if expected else [])


def test_br4_create_from_data_creates_accepted_reservation(monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb import rb_settings
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    import indico.modules.rb.models.reservations as reservation_module

    monkeypatch.setattr(reservation_module, 'notify_creation', lambda reservation: None)
    monkeypatch.setattr(reservation_module.signals.rb.booking_created, 'send', lambda *a, **kw: None)
    skipped_conflicts = []
    create_occurrences = Reservation.create_occurrences

    def create_occurrences_spy(self, skip_conflicts, *args, **kwargs):
        skipped_conflicts.append(skip_conflicts)
        return create_occurrences(self, skip_conflicts, *args, **kwargs)

    monkeypatch.setattr(Reservation, 'create_occurrences', create_occurrences_spy)
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    result = Reservation.create_from_data(room=dummy_room, data={
        'start_dt': start, 'end_dt': start + timedelta(hours=1),
        'repeat_frequency': RepeatFrequency.NEVER, 'repeat_interval': 0,
        'room_id': dummy_room.id, 'booking_reason': 'coverage case', 'recurrence_weekdays': None,
    }, user=dummy_user, prebook=False)

    assert result.state == ReservationState.accepted
    assert result.booked_for_user == dummy_user
    assert result.start_dt == start
    assert result.end_dt == start + timedelta(hours=1)
    assert skipped_conflicts == [True]


def test_br4_create_from_data_clamps_repeating_booking_to_first_and_last_occurrence(
        monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    import indico.modules.rb.models.reservations as reservation_module

    monkeypatch.setattr(reservation_module, 'notify_creation', lambda reservation: None)
    monkeypatch.setattr(reservation_module.signals.rb.booking_created, 'send', lambda *a, **kw: None)
    start = datetime.combine(date.today() + timedelta(days=2), time(10))
    until = start + timedelta(days=2, hours=1)
    result = Reservation.create_from_data(dummy_room, {
        'start_dt': start,
        'end_dt': until,
        'repeat_frequency': RepeatFrequency.DAY,
        'repeat_interval': 1,
        'room_id': dummy_room.id,
        'booking_reason': 'repeated coverage case',
    }, dummy_user, prebook=False)

    assert result.start_dt == start
    assert result.end_dt == until


def test_br4_create_from_data_rejects_mismatched_single_booking_dates(dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation

    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    data = {'start_dt': start, 'end_dt': start + timedelta(days=1), 'repeat_frequency': RepeatFrequency.NEVER}
    with pytest.raises(ValueError, match='end_dt != start_dt'):
        Reservation.create_from_data(dummy_room, data, dummy_user, prebook=False)


def test_br4_create_from_data_derives_direct_booking_and_internal_note(monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    import indico.modules.rb as rb_module
    import indico.modules.rb.models.reservations as reservation_module

    monkeypatch.setattr(reservation_module, 'notify_creation', lambda reservation: None)
    monkeypatch.setattr(reservation_module.signals.rb.booking_created, 'send', lambda *a, **kw: None)
    monkeypatch.setattr(rb_module.rb_settings, 'get', lambda key: key == 'internal_notes_enabled')
    monkeypatch.setattr(dummy_room, 'can_book', lambda user, allow_admin=True: True)
    monkeypatch.setattr(dummy_room, 'can_prebook', lambda user, allow_admin=True: False)
    monkeypatch.setattr(dummy_room, 'can_manage', lambda user, **kwargs: True)
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    result = Reservation.create_from_data(dummy_room, {
        'start_dt': start, 'end_dt': start + timedelta(hours=1),
        'repeat_frequency': RepeatFrequency.NEVER, 'repeat_interval': 0,
        'room_id': dummy_room.id, 'booking_reason': 'coverage case', 'recurrence_weekdays': None,
        'internal_note': 'internal', 'booked_for_user': None,
    }, dummy_user, prebook=None)
    assert result.state == ReservationState.accepted
    assert result.internal_note == 'internal'
    assert result.booked_for_user == dummy_user


def test_br4_create_from_data_does_not_include_internal_note_when_feature_disabled(
        monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    import indico.modules.rb as rb_module
    import indico.modules.rb.models.reservations as reservation_module

    monkeypatch.setattr(reservation_module, 'notify_creation', lambda reservation: None)
    monkeypatch.setattr(reservation_module.signals.rb.booking_created, 'send', lambda *a, **kw: None)
    monkeypatch.setattr(rb_module.rb_settings, 'get', lambda key: False)
    monkeypatch.setattr(dummy_room, 'can_manage', lambda user, **kwargs: True)
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    result = Reservation.create_from_data(dummy_room, {
        'start_dt': start,
        'end_dt': start + timedelta(hours=1),
        'repeat_frequency': RepeatFrequency.NEVER,
        'repeat_interval': 0,
        'room_id': dummy_room.id,
        'booking_reason': 'internal-note gate case',
        'internal_note': 'must not be copied',
    }, dummy_user, prebook=False)

    assert result.internal_note == ''


def test_br4_create_from_data_allows_direct_admin_override_by_default(
        monkeypatch, dummy_room, create_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation, ReservationState
    import indico.modules.rb.models.reservations as reservation_module

    admin = create_user(133, rb_admin=True)
    dummy_room.is_reservable = False
    monkeypatch.setattr(reservation_module, 'notify_creation', lambda reservation: None)
    monkeypatch.setattr(reservation_module.signals.rb.booking_created, 'send', lambda *a, **kw: None)
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    result = Reservation.create_from_data(dummy_room, {
        'start_dt': start,
        'end_dt': start + timedelta(hours=1),
        'repeat_frequency': RepeatFrequency.NEVER,
        'repeat_interval': 0,
        'room_id': dummy_room.id,
        'booking_reason': 'admin override case',
    }, admin)

    assert result.state == ReservationState.accepted


def test_br4_create_from_data_ignores_admin_override_when_requested(
        monkeypatch, dummy_room, create_user):
    from indico.core.db.sqlalchemy.protection import ProtectionMode
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation

    admin = create_user(134, rb_admin=True)
    dummy_room.is_reservable = False
    dummy_room.protection_mode = ProtectionMode.public
    dummy_room.reservations_need_confirmation = True
    start = datetime.combine(date.today() + timedelta(days=1), time(10))

    with pytest.raises(NoReportError, match='cannot book this room'):
        Reservation.create_from_data(dummy_room, {
            'start_dt': start,
            'end_dt': start + timedelta(hours=1),
            'repeat_frequency': RepeatFrequency.NEVER,
        }, admin, prebook=None, ignore_admin=True)


def test_br4_create_from_data_forwards_ignore_admin_to_room_checks(
        monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    import indico.modules.rb as rb_module
    import indico.modules.rb.models.reservations as reservation_module

    monkeypatch.setattr(reservation_module, 'notify_creation', lambda reservation: None)
    monkeypatch.setattr(reservation_module.signals.rb.booking_created, 'send', lambda *a, **kw: None)
    monkeypatch.setattr(rb_module.rb_settings, 'get', lambda key: key == 'internal_notes_enabled')
    manage_admin_flags = []
    advance_admin_flags = []
    occurrence_admin_flags = []
    monkeypatch.setattr(dummy_room, 'can_manage',
                        lambda user, **kwargs: manage_admin_flags.append(kwargs['allow_admin']) or
                        kwargs['allow_admin'])
    monkeypatch.setattr(dummy_room, 'check_advance_days',
                        lambda *args, **kwargs: advance_admin_flags.append(kwargs['allow_admin']))
    create_occurrences = Reservation.create_occurrences

    def create_occurrences_spy(self, *args, **kwargs):
        occurrence_admin_flags.append(kwargs['allow_admin'])
        return create_occurrences(self, *args, **kwargs)

    monkeypatch.setattr(Reservation, 'create_occurrences', create_occurrences_spy)
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    result = Reservation.create_from_data(dummy_room, {
        'start_dt': start,
        'end_dt': start + timedelta(hours=1),
        'repeat_frequency': RepeatFrequency.NEVER,
        'repeat_interval': 0,
        'room_id': dummy_room.id,
        'booking_reason': 'ignore admin case',
        'internal_note': 'must not be copied',
    }, dummy_user, prebook=False, ignore_admin=True)

    assert result.internal_note == ''
    assert manage_admin_flags and set(manage_admin_flags) == {False}
    assert advance_admin_flags == [False]
    assert occurrence_admin_flags == [False]


def test_br4_create_from_data_omits_optional_fields_when_absent(monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    import indico.modules.rb.models.reservations as reservation_module
    monkeypatch.setattr(reservation_module, 'notify_creation', lambda reservation: None)
    monkeypatch.setattr(reservation_module.signals.rb.booking_created, 'send', lambda *a, **kw: None)
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    result = Reservation.create_from_data(dummy_room, {
        'start_dt': start, 'end_dt': start + timedelta(hours=1),
        'repeat_frequency': RepeatFrequency.NEVER, 'repeat_interval': 0,
        'room_id': dummy_room.id, 'booking_reason': 'coverage case',
    }, dummy_user, prebook=False)
    assert result.recurrence_weekdays is None


def test_br4_create_from_data_rejects_user_without_room_permission(monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    monkeypatch.setattr(dummy_room, 'can_book', lambda user, allow_admin=True: False)
    monkeypatch.setattr(dummy_room, 'can_prebook', lambda user, allow_admin=True: False)
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    with pytest.raises(NoReportError, match='cannot book this room'):
        Reservation.create_from_data(dummy_room, {
            'start_dt': start, 'end_dt': start + timedelta(hours=1),
            'repeat_frequency': RepeatFrequency.NEVER,
        }, dummy_user, prebook=None)


def test_br4_create_from_data_rejects_when_all_occurrences_invalid(monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    import indico.modules.rb.models.reservations as reservation_module
    monkeypatch.setattr(Reservation, 'create_occurrences', lambda self, *a, **kw: None)
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    with pytest.raises(NoReportError, match='no valid occurrences'):
        Reservation.create_from_data(dummy_room, {
            'start_dt': start, 'end_dt': start + timedelta(hours=1),
            'repeat_frequency': RepeatFrequency.NEVER, 'repeat_interval': 0,
            'room_id': dummy_room.id, 'booking_reason': 'coverage case', 'recurrence_weekdays': None,
        }, dummy_user, prebook=False)


def test_br3_moderator_wrappers_accept_and_reject(monkeypatch):
    accepted, rejected = [], []
    actor = object()
    monkeypatch.setattr(backend, 'session', SimpleNamespace(user=actor))
    handler = _action_handler('approve', SimpleNamespace(
        accept=lambda user, reason=None: accepted.append((user, reason)),
        reject=lambda user, reason, silent=False: rejected.append((user, reason))))
    # Call the undecorated methods so the test exercises the handler behavior without
    # coupling it to request deserialization, which is covered by the API tests.
    RHBookingStateActions.accept.__wrapped__(handler, reason='ok', force=True)
    RHBookingStateActions.reject.__wrapped__(handler, reason='no')
    assert accepted == [(actor, 'ok')]
    assert rejected == [(actor, 'no')]


@pytest.mark.parametrize(('link_type', 'link_id'), ((None, 1), ('event', None)))
def test_br1_create_handler_ignores_incomplete_optional_link(monkeypatch, link_type, link_id):
    handler = _create_handler(monkeypatch)
    handler.args.update(link_type=link_type, link_id=link_id)
    linked = []
    handler._link_booking = lambda *args: linked.append(args)

    handler._process()

    assert linked == []


@pytest.mark.parametrize(('admin_override', 'expected_ignore_admin'), ((False, True), (True, False)))
def test_br1_create_handler_passes_admin_override_to_reservation(monkeypatch, admin_override, expected_ignore_admin):
    handler = _create_handler(monkeypatch)
    handler.args['admin_override_enabled'] = admin_override
    calls = []
    reservation = SimpleNamespace(occurrences=_OccurrenceList([SimpleNamespace(linked_object=None)]))
    monkeypatch.setattr(backend.Reservation, 'create_from_data',
                        lambda *args, **kwargs: (calls.append(kwargs) or reservation))

    handler._process()

    assert calls[0]['ignore_admin'] is expected_ignore_admin


@pytest.mark.parametrize('repeat_frequency', (1, 2, 3))
def test_br4_repeating_reservation_can_span_dates(monkeypatch, dummy_room, dummy_user, repeat_frequency):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
    import indico.modules.rb.models.reservations as reservation_module

    assert repeat_frequency in (RepeatFrequency.DAY, RepeatFrequency.WEEK, RepeatFrequency.MONTH)
    marker = RuntimeError('repeating booking reached occurrence creation')
    monkeypatch.setattr(Reservation, 'create_occurrences', lambda *args, **kwargs: (_ for _ in ()).throw(marker))
    start = datetime.combine(date.today() + timedelta(days=1), time(10))
    data = {
        'start_dt': start,
        'end_dt': start + timedelta(days=2),
        'repeat_frequency': repeat_frequency,
        'repeat_interval': 1,
        'room_id': dummy_room.id,
    }

    with pytest.raises(RuntimeError, match='reached occurrence creation'):
        Reservation.create_from_data(dummy_room, data, dummy_user, prebook=False)


def test_br4_single_booking_rejects_dates_in_reverse_order(monkeypatch, dummy_room, dummy_user):
    from indico.modules.rb.models.reservations import RepeatFrequency, Reservation

    marker = RuntimeError('invalid single-booking dates were accepted')
    monkeypatch.setattr(Reservation, 'create_occurrences', lambda *args, **kwargs: (_ for _ in ()).throw(marker))
    start = datetime.combine(date.today() + timedelta(days=2), time(10))
    data = {'start_dt': start, 'end_dt': start - timedelta(days=1), 'repeat_frequency': RepeatFrequency.NEVER}

    with pytest.raises(ValueError, match='end_dt != start_dt'):
        Reservation.create_from_data(dummy_room, data, dummy_user, prebook=False)


def test_br3_moderator_accept_collision_can_be_forced(monkeypatch):
    monkeypatch.setattr(backend, 'session', SimpleNamespace(user=object()))
    handler = _action_handler('approve', SimpleNamespace(accept=lambda *a, **kw: pytest.fail('must reject collision')))
    monkeypatch.setattr(backend, 'get_prebooking_collisions', lambda booking: ['collision'])
    monkeypatch.setattr(backend, 'reservation_occurrences_schema', SimpleNamespace(dump=lambda data: ['serialized']))
    with pytest.raises(Exception, match='prebooking_collision'):
        RHBookingStateActions.accept.__wrapped__(handler)
    accepted = []
    handler.booking.accept = lambda *a, **kw: accepted.append(kw)
    RHBookingStateActions.accept.__wrapped__(handler, force=True)
    assert accepted


def test_br3_moderator_accept_without_collision(monkeypatch):
    actor = object()
    monkeypatch.setattr(backend, 'session', SimpleNamespace(user=actor))
    monkeypatch.setattr(backend, 'get_prebooking_collisions', lambda booking: [])
    accepted = []
    handler = _action_handler('approve', SimpleNamespace(accept=lambda user, reason: accepted.append(user)))
    RHBookingStateActions.accept.__wrapped__(handler, reason=None, force=False)
    assert accepted == [actor]
