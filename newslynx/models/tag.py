from sqlalchemy.dialects.postgresql import ENUM

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.text import slug
from newslynx.constants import (
    IMPACT_TAG_CATEGORIES, IMPACT_TAG_LEVELS, TAG_TYPES)


class Tag(db.Model):

    """
    A tag is an arbitrary label which we can assign
    to a content-item or an event.
    """

    __tablename__ = 'tags'
    __module__ = 'newslynx.models.tag'

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    name = db.Column(db.Text)
    slug = db.Column(db.Text, index=True)
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)
    color = db.Column(db.Text)
    type = db.Column(ENUM(*TAG_TYPES, name='tag_type_enum'))
    category = db.Column(ENUM(*IMPACT_TAG_CATEGORIES, name='tag_categories_enum'))
    level = db.Column(ENUM(*IMPACT_TAG_LEVELS, name='tag_levels_enum'))

    __table_args__ = (
        db.UniqueConstraint('org_id', 'slug', 'type'),
    )

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.name = kw.get('name')
        self.slug = slug(kw.get('slug', kw['name']))
        self.type = kw.get('type')
        self.color = kw.get('color')
        self.category = kw.get('category')
        self.level = kw.get('level')

    def to_dict(self, **kw):
        incl_counts = kw.get('incl_counts', True)

        if self.type == 'impact':
            d = {
                'id': self.id,
                'org_id': self.org_id,
                'name': self.name,
                'slug': self.slug,
                'type': self.type,
                'color': self.color.lower(),
                'category': self.category,
                'level': self.level,
                'created': self.created,
                'updated': self.updated
            }
            if incl_counts:
                d['event_count'] = self.events.count()
        else:
            d = {
                'id': self.id,
                'org_id': self.org_id,
                'name': self.name,
                'slug': self.slug,
                'type': self.type,
                'color': self.color.lower(),
                'created': self.created,
                'updated': self.updated
            }
            if incl_counts:
                d['content_item_count'] = self.content_items.count()
        return d

    def __repr__(self):

        return '<Tag %r / %r >' % (self.name, self.type)
