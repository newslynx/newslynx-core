from sqlalchemy.dialects.postgresql import JSON, ENUM
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy import Index

from newslynx.core import db, SearchQuery
from newslynx.lib import dates
from newslynx.models import relations
from newslynx.taxonomy import THING_TYPES


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
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), index=True)
    type = db.Column(ENUM(*THING_TYPES, name='thing_types_enum'))
    url = db.Column(db.Text, index=True, unique=True)
    domain = db.Column(db.Text, index=True)
    created = db.Column(db.DateTime(timezone=True), index=True)
    updated = db.Column(db.DateTime(timezone=True), index=True)
    img_url = db.Column(db.Text)
    byline = db.Column(db.Text)
    title = db.Column(db.Text, index=True)
    description = db.Column(db.Text, index=True)
    text = db.Column(db.Text, index=True)
    source_html = db.Column(db.Text)
    meta = db.Column(JSON)

    # our search vector
    search_vector = db.Column(TSVectorType('title', 'description', 'text', 'type', 'byline', 'meta'))

    # relations
    tags = db.relationship(
        'Tag', secondary=relations.things_tags,
        backref=db.backref('things', lazy='dynamic'), lazy='joined')

    events = db.relationship('Event',
                             secondary=relations.things_events,
                             backref=db.backref('things', lazy='dynamic'),
                             lazy='dynamic')

    # relations
    creators = db.relationship(
        'Creator', secondary=relations.things_creators,
        backref=db.backref('things', lazy='dynamic'), lazy='joined')

    __table_args__ = (
        Index('things_search_vector_idx', 'search_vector', postgresql_using='gin'),
    )

    def __init__(self, **kw):
        self.organization_id = kw.get('organization_id')
        self.recipe_id = kw.get('recipe_id')
        self.url = kw.get('url')
        self.type = kw.get('type')
        self.domain = kw.get('domain')
        self.created = kw.get('published', dates.now())
        self.updated = kw.get('last_updated', dates.now())
        self.img_url = kw.get('img_url')
        self.byline = kw.get('byline') ## TODO: Autoformat.
        self.title = kw.get('title')
        self.description = kw.get('description')
        self.text = kw.get('text')
        self.meta = kw.get('meta', {})

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'recipe_id': self.recipe_id,
            'url': self.url,
            'domain': self.domain,
            'type': self.type,
            'created': self.created,
            'updated': self.updated,
            'img_url': self.img_url,
            'creators': [c.to_dict() for c in self.creators],
            'title': self.title,
            'description': self.description,
            'text': self.text,
            'source_html': self.source_html,
            'meta': self.meta
        }

    def __repr__(self):
        return '<Thing %r >' % (self.url)
