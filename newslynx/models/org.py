import copy
from sqlalchemy.dialects.postgresql import ENUM

from slugify import slugify

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.serialize import json_to_obj
from newslynx.models.relations import orgs_users


class Org(db.Model):

    __tablename__ = 'orgs'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    name = db.Column(db.Text, unique=True, index=True)
    slug = db.Column(db.Text, unique=True, index=True)
    timezone = db.Column(ENUM(*list(dates.TIMEZONES), name='org_timezones_enum'))
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    # joins
    auths = db.relationship('Auth',
                            backref=db.backref('org'),
                            lazy='joined',
                            cascade="all, delete-orphan")
    settings = db.relationship('Setting',
                               backref=db.backref('org'),
                               lazy='joined',
                               cascade="all, delete-orphan")

    # dynamic relations
    users = db.relationship(
        'User', secondary=orgs_users,
        backref=db.backref('orgs', lazy='joined'),
        lazy='joined')
    events = db.relationship('Event', lazy='dynamic', cascade='all')
    content_items = db.relationship('ContentItem', lazy='dynamic', cascade='all')
    metrics = db.relationship('Metric', lazy='dynamic', cascade='all')
    recipes = db.relationship('Recipe', lazy='dynamic', cascade='all')
    authors = db.relationship('Author', lazy='dynamic')
    tags = db.relationship('Tag', lazy='dynamic', cascade='all')

    def __init__(self, **kw):
        self.name = kw.get('name')
        self.timezone = kw.get('timezone', 'UTC')
        self.slug = kw.get('slug', slugify(kw['name']))

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
    def metrics_lookup(self):
        lookup = {}
        for m in self.metrics:
            m = m.to_dict()
            name = m.pop('name')
            lookup[name] = m
        return lookup

    @property
    def user_ids(self):
        return [u.id for u in self.users]

    def to_dict(self, **kw):

        # parse kwargs
        incl_users = kw.get('incl_users', True)
        incl_settings = kw.get('incl_settings', True)
        incl_tags = kw.get('incl_tags', False)
        incl_auths = kw.get('incl_auths', True)
        settings_as_dict = kw.get('settings_dict', True)

        d = {
            'id': self.id,
            'name': self.name,
            'timezone': self.timezone,
            'slug': self.slug,
            'created': self.created,
            'updated': self.updated
        }
        if incl_users:
            d['users'] = [
                u.to_dict(incl_org=False, incl_apikey=False) for u in self.users]
        if incl_settings:
            if settings_as_dict:
                d['settings'] = self.settings_dict
            else:
                d['settings'] = self.settings
        if incl_auths:
            d['auths'] = self.auths
        if incl_tags:
            d['tags'] = [t.to_dict() for t in self.tags.query.all()]
        return d

    def __repr__(self):
        return "<Org %s >" % (self.name)
