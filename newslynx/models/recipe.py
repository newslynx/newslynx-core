from sqlalchemy.dialects.postgresql import JSON, ENUM
from slugify import slugify

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.serialize import obj_to_pickle, pickle_to_obj
from newslynx.constants import RECIPE_STATUSES


class Recipe(db.Model):

    __tablename__ = 'recipes'

    # id fields
    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    sous_chef_id = db.Column(
        db.Integer, db.ForeignKey('sous_chefs.id'), index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), index=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)

    # metadata fields
    name = db.Column(db.Text, index=True)
    slug = db.Column(db.Text, index=True)
    description = db.Column(db.Text)

    # date fields
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)
    last_run = db.Column(db.DateTime(timezone=True), index=True)

    # scheduler fields
    scheduled = db.Column(db.Boolean, index=True)
    time_of_day = db.Column(db.Text, index=True)
    interval = db.Column(db.Integer, index=True)
    status = db.Column(
        ENUM(*RECIPE_STATUSES, name="enum_recipe_statuses"), index=True)
    last_job = db.Column(JSON)

    # options
    options = db.Column(db.Text)

    # relations
    events = db.relationship('Event', lazy='dynamic')
    content_items = db.relationship('ContentItem', lazy='dynamic')
    metrics = db.relationship('Metric', lazy='joined')
    sous_chef = db.relationship(
        'SousChef', backref=db.backref('recipes', lazy='joined', cascade="all, delete-orphan"), lazy='joined')
    user = db.relationship(
        'User', backref=db.backref('recipes', lazy='dynamic'), lazy='joined')

    __table_args__ = (
        db.UniqueConstraint('org_id', 'slug'),
    )

    def __init__(self, sous_chef, **kw):
        """
        A recipe must be initialized with an existing sous chef.
        """
        # core fields
        self.name = kw.get('name')
        self.slug = slugify(kw.get('slug', kw['name']))
        self.description = kw.get('description')
        self.time_of_day = kw.get('time_of_day')
        self.interval = kw.get('interval')
        self.status = kw.get('status', 'stable')
        self.set_options(kw.get('options', {}))

        # internal fields
        self.sous_chef_id = sous_chef.id
        self.user_id = kw.get('user_id')
        self.org_id = kw.get('org_id')
        self.scheduled = kw.get('scheduled', False)
        self.last_run = kw.get('last_run', None)
        self.last_job = kw.get('last_job', {})

    def set_options(self, opts):
        """
        pickle dump the options.
        """
        self.options = obj_to_pickle(opts)

    def to_dict(self, incl_sous_chef=False):
        d = {
            'id': self.id,
            'org_id': self.org_id,
            'sous_chef': self.sous_chef.slug,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'created': self.created,
            'updated': self.updated,
            'last_run': self.last_run,
            'scheduled': self.scheduled,
            'time_of_day': self.time_of_day,
            'interval': self.interval,
            'status': self.status,
            'last_job': self.last_job,
            'options': pickle_to_obj(self.options)
        }
        if self.sous_chef.creates == 'metrics':
            d['metrics'] = self.metrics
        return d

    def __repr__(self):
        return '<Recipe %r >' % (self.slug)
