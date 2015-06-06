from sqlalchemy.dialects.postgresql import JSON, ENUM
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy import Index

from newslynx.core import db, SearchQuery
from newslynx.lib import dates
from newslynx.models import relations
from newslynx.constants import (
    THING_TYPES, THING_PROVENANCES)


class Thing(db.Model):

    """
    A thing is a unit of content
    to which we attach metrics.

    We do not initialize a thing until we have past it completely through
    our single extraction pipeline.

    At this point all things should have a standardized schema,
    though may not have all theses fields filled in.
    """

    query_class = SearchQuery

    __tablename__ = 'things'

    # the ID is the global bitly hash.
    id = db.Column(db.Integer, unique=True, primary_key=True, index=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), index=True)
    type = db.Column(ENUM(*THING_TYPES, name='thing_types_enum'))
    provenance = db.Column(
        ENUM(*THING_PROVENANCES, name='thing_provenance_enum'), index=True)
    url = db.Column(db.Text, index=True)
    domain = db.Column(db.Text, index=True)
    created = db.Column(db.DateTime(timezone=True), index=True)
    updated = db.Column(db.DateTime(timezone=True), index=True)
    img_url = db.Column(db.Text)
    byline = db.Column(db.Text)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    body = db.Column(db.Text)
    meta = db.Column(JSON)

    # our search vector
    search_vector = db.Column(
        TSVectorType('title', 'description', 'body', 'type', 'byline', 'meta'))

    # relations
    tags = db.relationship(
        'Tag', secondary=relations.things_tags,
        backref=db.backref('things', lazy='dynamic'), lazy='joined')

    events = db.relationship('Event',
                             secondary=relations.things_events,
                             backref=db.backref('things', lazy='dynamic'),
                             lazy='dynamic')

    creators = db.relationship(
        'Creator', secondary=relations.things_creators,
        backref=db.backref('things', lazy='dynamic'), lazy='joined')

    # in/out links
    out_links = db.relationship(
        'Thing', secondary=relations.things_things,
        primaryjoin=relations.things_things.c.from_thing_id == id,
        secondaryjoin=relations.things_things.c.to_thing_id == id,
        backref=db.backref("in_links", lazy='dynamic'),
        lazy='dynamic')

    # things should be unique to org, url, and type.
    # IE there might be multiple things per url -
    # an article, a video, a podcast, etc.
    __table_args__ = (
        db.UniqueConstraint(
            'org_id', 'url', 'type', name='thing_unique_constraint'),
        Index('things_search_vector_idx',
              'search_vector', postgresql_using='gin')
    )

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.recipe_id = kw.get('recipe_id')
        self.url = kw.get('url')
        self.type = kw.get('type')
        self.provenance = kw.get('provenance', 'recipe')
        self.domain = kw.get('domain')
        self.created = kw.get('created', dates.now())
        self.updated = kw.get('updated', dates.now())
        self.img_url = kw.get('img_url')
        self.byline = kw.get('byline')  # TODO: Autoformat.
        self.title = kw.get('title')
        self.description = kw.get('description')
        self.body = kw.get('body')
        self.meta = kw.get('meta', {})

    @property
    def simple_creators(self):
        return [{"id": c.id, "name": c.name} for c in self.creators]

    @property
    def out_link_ids(self):
        out_links = db.session.query(relations.things_things.c.to_thing_id)\
            .filter(relations.things_things.c.from_thing_id == self.id)\
            .all()
        return [o[0] for o in out_links]

    @property
    def in_link_ids(self):
        in_links = db.session.query(relations.things_things.c.from_thing_id)\
            .filter(relations.things_things.c.to_thing_id == self.id)\
            .all()
        return [o[0] for o in in_links]

    @property
    def out_link_display(self):
        out_links = self.out_links\
            .with_entities(Thing.id, Thing.title)\
            .all()
        return [dict(zip(['id', 'title'], l)) for l in out_links]

    @property
    def in_link_display(self):
        in_links = self.in_links\
            .with_entities(Thing.id, Thing.title)\
            .all()
        return [dict(zip(['id', 'title'], l)) for l in in_links]

    @property
    def tag_ids(self):
        return [t.id for t in self.tags]

    def to_dict(self, **kw):
        d = {
            'id': self.id,
            'org_id': self.org_id,
            'recipe_id': self.recipe_id,
            'url': self.url,
            'domain': self.domain,
            'provenance': self.provenance,
            'type': self.type,
            'created': self.created,
            'updated': self.updated,
            'img_url': self.img_url,
            'creators': self.simple_creators,
            'title': self.title,
            'description': self.description,
            'tag_ids': self.tag_ids,
            'meta': self.meta
        }
        if kw.get('incl_links', False):
            d['in_links'] = self.in_link_display
            d['out_links'] = self.out_link_display
        if kw.get('incl_body', False):
            d['body'] = self.body
        return d

    def __repr__(self):
        return '<Thing %r >' % (self.url)
