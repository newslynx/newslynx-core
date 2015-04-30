import copy

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.serialize import json_to_obj
from newslynx.models.relations import organizations_users


class Organization(db.Model):

    __tablename__ = 'organizations'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    name = db.Column(db.Text, unique=True, index=True)
    created = db.Column(db.DateTime(timezone=True))

    # relations
    authorizations = db.relationship('Auth',
                                     backref=db.backref('organization'),
                                     lazy='joined',
                                     cascade="all, delete-orphan")
    users = db.relationship('User',
                            secondary=organizations_users,
                            backref=db.backref('organizations', lazy='joined'),
                            lazy='joined')
    settings = db.relationship('Setting',
                               backref=db.backref('organization'),
                               lazy='joined',
                               cascade="all, delete-orphan")
    events = db.relationship('Event',
                             lazy='dynamic',
                             cascade='all')
    things = db.relationship('Thing',
                             lazy='dynamic',
                             cascade='all')
    metrics = db.relationship('Metric',
                              lazy='dynamic',
                              cascade='all')
    recipes = db.relationship('Recipe',
                              lazy='dynamic',
                              cascade='all')
    creators = db.relationship('Creator', lazy='dynamic')

    tags = db.relationship('Tag', lazy='dynamic')

    def __init__(self, **kw):
        self.name = kw.get('name')
        self.created = kw.get('created', dates.now())

    @property
    def settings_dict(self):
        settings = {}
        for s in self.settings:
            if s.json_value:
                v = json_to_obj(s.value)
            else:
                v = copy.copy(s.value)
            settings[s.name] = v
        return settings

    @property
    def user_ids(self):
        return frozenset([u.id for u in self.users])

    def to_dict(self, incl_users=True, incl_settings=True, incl_authorizations=True):
        d = {
            'id': self.id,
            'name': self.name
        }
        if incl_users:
            d['users'] = [
                u.to_dict(incl_org=False, incl_apikey=False) for u in self.users]
        if incl_settings:
            d['settings'] = self.settings
        if incl_authorizations:
            d['authorizations'] = self.authorizations
        return d

    def __repr__(self):
        return "<Organization %s >" % (self.name)
