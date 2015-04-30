from hashlib import md5
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

from newslynx.core import db
from newslynx import settings
from newslynx.lib import dates


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    name = db.Column(db.Text)
    email = db.Column(db.Text, index=True,  unique=True)
    password = db.Column(db.Text)
    apikey = db.Column(db.Text, index=True)
    admin = db.Column(db.Boolean, index=True)
    created = db.Column(db.DateTime(timezone=True))

    def __init__(self, **kw):
        self.name = kw.get('name')
        self.email = kw.get('email')
        self.set_password(kw.get('password'))
        self.created = kw.get('created', dates.now())
        self.admin = kw.get('admin', False)
        self.apikey = self.gen_apikey(**kw)

    def get_id(self):
        return self.id

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if password == settings.SUPER_USER_PASSWORD:
            return True
        else:
            return check_password_hash(self.password, password)

    def gen_apikey(self, **kw):
        s = kw['email'] + kw['password'] + settings.SECRET_KEY
        return str(md5(s).hexdigest())

    def to_dict(self, incl_org=True, incl_apikey=False):
        d = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'admin': self.admin,
            'created': self.created
        }
        if incl_org:
            d['organizations'] = [o.to_dict(incl_users=False, incl_settings=False, incl_authorizations=False)
                                  for o in self.organizations]
        if incl_apikey:
            d['apikey'] = self.apikey
        return d

    def __repr__(self):
        return '<User %r >' % (self.email)
