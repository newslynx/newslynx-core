from sqlalchemy.dialects.postgresql import JSON, ARRAY, ENUM
from sqlalchemy import Index
from sqlalchemy.types import String
from sqlalchemy_utils.types import TSVectorType

from newslynx.core import db, SearchQuery
from newslynx.lib import dates
from newslynx.models import relations
from newslynx.taxonomy import EVENT_STATUSES


class Event(db.Model):

    """
    An event is a significant moment in the life of a thing / organization.
    """

    query_class = SearchQuery

    __tablename__ = 'events'

    id = db.Column(db.Integer, unique=True, primary_key=True, index=True)
    # the unique id from the source.
    source_id = db.Column(db.Text, index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), index=True)
    status = db.Column(
        ENUM(*EVENT_STATUSES, name='event_status_enum'), index=True)
    url = db.Column(db.Text, index=True)
    img_url = db.Column(db.Text)
    created = db.Column(db.DateTime(timezone=True), index=True)
    updated = db.Column(db.DateTime(timezone=True), index=True)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    text = db.Column(db.Text)
    authors = db.Column(ARRAY(String))
    meta = db.Column(JSON)

    # our search vector
    search_vector = db.Column(
        TSVectorType('title', 'description', 'text', 'authors', 'meta'))

    # relations
    tags = db.relationship('Tag',
                           secondary=relations.events_tags,
                           backref=db.backref('events', lazy='dynamic'),
                           lazy='joined')

    # relations

    __table_args__ = (
        db.UniqueConstraint(
            'source_id', 'organization_id', 'recipe_id', name='event_unique_constraint'),
        Index('events_search_vector_idx',
              'search_vector', postgresql_using='gin')
    )

    def __init__(self, **kw):
        self.source_id = str(kw.get('source_id'))
        self.recipe_id = kw.get('recipe_id')
        self.organization_id = kw.get('organization_id')
        self.status = kw.get('status', 'pending')
        self.url = kw.get('url')
        self.img_url = kw.get('img_url')
        self.created = kw.get('created', dates.now())
        self.updated = kw.get('updated', dates.now())
        self.title = kw.get('title')
        self.description = kw.get('description')
        self.text = kw.get('text')
        self.authors = kw.get('authors', [])
        self.meta = kw.get('meta', {})

    @property
    def simple_things(self):
        things = []
        for t in self.things:
            things.append({
                'id': t.id,
                'title': t.title,
                'url': t.url
            })
        return things

    @property
    def thing_ids(self):
        return [t.id for t in self.things]

    @property
    def tag_ids(self):
        return [t.id for t in self.tags]

    @property
    def tag_count(self):
        return len(self.tags)

    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'recipe_id': self.recipe_id,
            'organization_id': self.organization_id,
            'status': self.status,
            'url': self.url,
            'img_url': self.img_url,
            'created': self.created,
            'updated': self.updated,
            'title': self.title,
            'description': self.description,
            'text': self.text,
            'authors': self.authors,
            'meta': self.meta,
            'tags': self.tags,
            'things': self.simple_things,
            'task': self.recipe.task.name
        }

    def __repr__(self):
        return '<Event %r>' % (self.title)
