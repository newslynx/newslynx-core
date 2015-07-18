from sqlalchemy.dialects.postgresql import JSON, ARRAY, ENUM
from sqlalchemy import Index
from sqlalchemy.types import String
from sqlalchemy_utils.types import TSVectorType

from newslynx.core import db, SearchQuery
from newslynx.lib import dates
from newslynx.lib import url
from newslynx.models import relations
from newslynx.constants import (
    EVENT_STATUSES, EVENT_PROVENANCES)


class Event(db.Model):

    """
    An event is a significant moment in the life of a thing / org.
    """

    query_class = SearchQuery

    __tablename__ = 'events'
    __module__ = 'newslynx.models.event'

    id = db.Column(db.Integer, unique=True, primary_key=True, index=True)
    # the unique id from the source.
    source_id = db.Column(db.Text, index=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), index=True)
    status = db.Column(
        ENUM(*EVENT_STATUSES, name='event_status_enum'), index=True)
    provenance = db.Column(
        ENUM(*EVENT_PROVENANCES, name='event_provenance_enum'), index=True)
    url = db.Column(db.Text, index=True)
    domain = db.Column(db.Text, index=True)
    img_url = db.Column(db.Text)
    thumbnail = db.Column(db.Text)
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    body = db.Column(db.Text)
    authors = db.Column(ARRAY(String))
    meta = db.Column(JSON)

    # search vectors
    title_search_vector = db.Column(TSVectorType('title'))
    description_search_vector = db.Column(TSVectorType('description'))
    body_search_vector = db.Column(TSVectorType('body'))
    authors_search_vector = db.Column(TSVectorType('authors'))
    meta_search_vector = db.Column(TSVectorType('meta'))

    # relations
    tags = db.relationship('Tag',
                           secondary=relations.events_tags,
                           backref=db.backref('events', lazy='dynamic'),
                           lazy='joined')

    # relations

    __table_args__ = (
        db.UniqueConstraint(
            'source_id', 'org_id', name='event_unique_constraint'),
        Index('events_title_search_vector_idx',
              'title_search_vector', postgresql_using='gin'),
        Index('events_description_search_vector_idx',
              'description_search_vector', postgresql_using='gin'),
        Index('events_body_search_vector_idx',
              'body_search_vector', postgresql_using='gin'),
        Index('events_authors_search_vector_idx',
              'authors_search_vector', postgresql_using='gin'),
        Index('events_meta_search_vector_idx',
              'meta_search_vector', postgresql_using='gin')
    )

    def __init__(self, **kw):
        self.source_id = str(kw.get('source_id'))
        self.recipe_id = kw.get('recipe_id')
        self.org_id = kw.get('org_id')
        self.status = kw.get('status', 'pending')
        self.provenance = kw.get('provenance', 'recipe')
        self.url = kw.get('url')
        self.domain = kw.get('domain', url.get_domain(kw.get('url', None)))
        self.img_url = kw.get('img_url')
        self.thumbnail = kw.get('thumbnail')
        self.created = kw.get('created', dates.now())
        self.title = kw.get('title')
        self.description = kw.get('description')
        self.body = kw.get('body')
        self.authors = kw.get('authors', [])
        self.meta = kw.get('meta', {})

    @property
    def simple_content_items(self):
        content_items = []
        for t in self.content_items:
            content_items.append({
                'id': t.id,
                'title': t.title,
                'url': t.url
            })
        return content_items

    @property
    def content_item_ids(self):
        return [t.id for t in self.content_items]

    @property
    def tag_ids(self):
        return [t.id for t in self.tags]

    @property
    def tag_count(self):
        return len(self.tags)

    def to_dict(self, **kw):
        d = {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'source_id': self.source_id,
            'status': self.status,
            'provenance': self.provenance,
            'url': self.url,
            'created': self.created,
            'updated': self.updated,
            'title': self.title,
            'description': self.description,
            'authors': self.authors,
            'meta': self.meta,
            'tag_ids': self.tag_ids,
            'content_items': self.simple_content_items,
        }
        if kw.get('incl_body', False):
            d['body'] = self.body
        if kw.get('incl_img', False):
            d['thumbnail'] = self.thumbnail
            d['img_url'] = self.img_url
        return d

    def __repr__(self):
        return '<Event %r>' % (self.title)
