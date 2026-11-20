"""Seed synthetic Room Booking test data into a running Indico instance.

Run inside the indico-web container:
    docker compose exec -T indico-web /opt/indico/.venv/bin/python - < tests/team/seed/seed_rb.py

Creates (idempotent):
  * users  admin / user1 / mgr1  (local login, password = "<username>-Pass123!")
  * location "SQE Campus" and room "R1" (reservable, public, needs confirmation, booking_limit_days=7)
  * mgr1 gets the room-level "moderate" permission on R1 (owner field grants nothing in Indico)
  * a personal API token (scope full:everything) for user1 and mgr1
Writes the tokens and ids as JSON to stdout (last line) so tests can read them.
All data is synthetic.
"""
import json

from indico.web.flask.app import make_app

app = make_app()

with app.app_context():
    from indico.core.db import db
    from indico.core.db.sqlalchemy.protection import ProtectionMode
    from indico.core.oauth.models.personal_tokens import PersonalToken
    from indico.modules.auth.models.identities import Identity
    from indico.modules.rb.models.locations import Location
    from indico.modules.rb.models.rooms import Room
    from indico.modules.users.operations import create_user

    USERS = {
        'admin': dict(first_name='Ada', last_name='Admin', is_admin=True),
        'user1': dict(first_name='Uma', last_name='User', is_admin=False),
        'mgr1': dict(first_name='Max', last_name='Manager', is_admin=False),
    }

    users = {}
    for username, data in USERS.items():
        ident = Identity.query.filter_by(provider='indico', identifier=username).first()
        if ident:
            users[username] = ident.user
            continue
        identity = Identity(provider='indico', identifier=username, password=f'{username}-Pass123!')
        user = create_user(f'{username}@sqe.example.invalid',
                           {'first_name': data['first_name'], 'last_name': data['last_name'],
                            'affiliation': 'SQE Test'},
                           identity=identity, from_moderation=True)
        user.is_admin = data['is_admin']
        users[username] = user
    db.session.flush()

    location = Location.query.filter_by(name='SQE Campus', is_deleted=False).first()
    if not location:
        location = Location(name='SQE Campus')
        db.session.add(location)
        db.session.flush()

    room = Room.query.filter_by(location=location, verbose_name='R1', is_deleted=False).first()
    if not room:
        room = Room(location=location, verbose_name='R1', building='1', floor='1', number='101',
                    capacity=10, owner=users['admin'])
        db.session.add(room)
    room.is_reservable = True
    room.protection_mode = ProtectionMode.public
    room.reservations_need_confirmation = True
    room.booking_limit_days = 7
    room.max_advance_days = None
    room.update_principal(users['mgr1'], permissions={'moderate'})
    db.session.flush()

    tokens = {}
    for username in ('user1', 'mgr1'):
        user = users[username]
        old = PersonalToken.query.filter_by(user=user, name='sqe-tests', revoked_dt=None).first()
        if old:
            old.revoke()
        tok = PersonalToken(user=user, name='sqe-tests', scopes={'full:everything'})
        db.session.add(tok)
        tokens[username] = tok.generate_token()

    db.session.commit()
    print(json.dumps({
        'room_id': room.id,
        'location_id': location.id,
        'users': {k: v.id for k, v in users.items()},
        'tokens': tokens,
    }))
