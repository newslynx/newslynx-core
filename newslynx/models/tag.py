from sqlalchemy.dialects.postgresql import ENUM

from newslynx.core import db
from newslynx.taxonomy import (
    IMPACT_TAG_CATEGORIES, IMPACT_TAG_LEVELS, TAG_TYPES)


class Tag(db.Model):

    """
    A tag is an arbitrary label (with arbitrary attributes)
    which we can assign to a thing or an event.
    """

    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), index=True)
    name = db.Column(db.Text, index=True)
    color = db.Column(db.Text)
    type = db.Column(ENUM(*TAG_TYPES, name='tag_type_enum'), index=True)
    category = db.Column(ENUM(*IMPACT_TAG_CATEGORIES, name='tag_categories_enum'))
    level = db.Column(ENUM(*IMPACT_TAG_LEVELS, name='tag_levels_enum'))

    __table_args__ = (
        db.UniqueConstraint('organization_id', 'name'),
    )

    def __init__(self, **kw):
        self.organization_id = kw.get('organization_id')
        self.name = kw.get('name')
        self.type = kw.get('type')
        self.color = kw.get('color')
        self.category = kw.get('category')
        self.level = kw.get('level')

    def to_dict(self):
        if self.type == 'impact':
            return {
                'id': self.id,
                'organization_id': self.organization_id,
                'name': self.name,
                'type': self.type,
                'color': self.color,
                'category': self.category,
                'level': self.level
            }
        else:
            return {
                'id': self.id,
                'organization_id': self.organization_id,
                'name': self.name,
                'type': self.type,
                'color': self.color,
            }

    def __repr__(self):

        return '<Tag %r / %r >' % (self.name, self.type)
