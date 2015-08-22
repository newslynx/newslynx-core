from hashlib import md5
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

from newslynx.core import db
from newslynx.core import settings
from newslynx.client import API
from newslynx.lib import dates
from uuid import uuid4


class User(db.Model):

    __tablename__ = 'users'
    __module__ = 'newslynx.models.user'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    name = db.Column(db.Text)
    email = db.Column(db.Text, index=True,  unique=True)
    password = db.Column(db.Text)
    apikey = db.Column(db.Text, index=True)
    admin = db.Column(db.Boolean, index=True)
    super_user = db.Column(db.Boolean, index=True)
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    _settings = db.relationship(
        'Setting',
        backref=db.backref('user'),
        lazy='dynamic',
        cascade="all, delete-orphan")

    def __init__(self, **kw):
        self.name = kw.get('name')
        self.email = kw.get('email')
        self.set_password(kw.get('password'))
        self.created = kw.get('created', dates.now())
        self.admin = kw.get('admin', kw.get('super_user', False))  # super users are also admins.
        self.super_user = kw.get('super_user', False)
        self.set_apikey(**kw)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if password == settings.SUPER_USER_PASSWORD:
            return True
        else:
            return check_password_hash(self.password, password)

    def set_apikey(self, **kw):
        s = str(uuid4()) + settings.SECRET_KEY
        self.apikey = str(md5(s).hexdigest())

    def get_settings(self, org_id):
        return self._settings.filter_by(level='me', user_id=self.id, org_id=org_id).all()

    @property
    def settings_dict(self):
        return {s['name']: s['value'] for s in self._settings.filter_by(level='me')}

    @property
    def display_orgs(self):
        return [o.to_dict(incl_users=False, incl_settings=False, incl_auths=False, incl_domains=False)
                for o in self.orgs]

    @property
    def org_ids(self):
        return [o.id for o in self.orgs]

    def get_api(self):
        return API(apikey=self.apikey)

    def to_dict(self, **kw):
        incl_org = kw.get('incl_org', True)
        incl_apikey = kw.get('incl_apikey', False)
        incl_settings = kw.get('incl_settings', False)

        d = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'admin': self.admin,
            'super_user': self.super_user,
            'created': self.created,
            'updated': self.updated
        }

        if incl_org:
            d['orgs'] = self.display_orgs

        if incl_apikey:
            d['apikey'] = self.apikey

        if incl_settings:
            d['settings'] = self.settings_dict

        return d

    def __repr__(self):
        return '<User %r >' % (self.email)
