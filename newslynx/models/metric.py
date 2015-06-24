from sqlalchemy.dialects.postgresql import ENUM, ARRAY

from newslynx.core import db
from newslynx.lib import dates
from newslynx.constants import (
    METRIC_CONTENT_LEVELS, METRIC_ORG_LEVELS,
    METRIC_TYPES
)


class Metric(db.Model):

    """
    A metric is a concept created by a recipe and (ultimately) associated with
    an org or an org and a content-item.

    Metrics MUST have the following metadata:
        - A associated recipe id.
        - A unique name
        - A unique slug (separated with underscores.)
        - A function which we use to aggregate it.
            - sum (for counts) => pageviews, share counts, unique visitors, etc.
            - mean (for averages) => time on page / percent external traffic, etc.
            - median (for averages) => time on page / percent external traffic, etc.
            - min/max => (for ranks) (position on homepage, etc)
        - A boolean indicating whether or not it is a timeseries (twiter shares / followers)
        - A boolean indicating whether or not it is cumulative (twiter shares / followers)
        - A boolean indicating whether or not it is a faceted metric. (pageviews per domain)
        - A level at which it applies (content_item  / org).

    Metrics are only created in SousChef configurations.
    For instance, the Google Analytics Sous Chef will
    specify metadata about pageviews / time on page / entrances / exits / etc.

    When a recipe associated with this sous chef is created, records for each
    of these metrics will be inserted into this table.
    """

    __tablename__ = 'metrics'
    __module__ = 'newslynx.models.metric'

    id = db.Column(db.Integer, unique=True, primary_key=True, index=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True
    )
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), index=True)
    name = db.Column(db.Text, index=True)
    display_name = db.Column(db.Text)
    type = db.Column(ENUM(*METRIC_TYPES, name='metric_types_enum'), index=True)
    content_levels = db.Column(ARRAY(db.Text), index=True)
    org_levels = db.Column(ARRAY(db.Text), index=True)
    faceted = db.Column(db.Boolean, index=True, default=False)
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    __table_args__ = (
        db.UniqueConstraint('org_id', 'name', 'type'),
    )

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.recipe_id = kw.get('recipe_id')
        self.name = kw.get('name')
        self.display_name = kw.get('display_name')
        self.type = kw.get('type')
        self.content_levels = kw.get('content_levels', [])
        self.org_levels = kw.get('org_levels', [])
        self.faceted = kw.get('faceted', False)

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'recipe_id': self.recipe_id,
            'name': self.name,
            'display_name': self.display_name,
            'type': self.type,
            'content_levels': self.content_levels,
            'org_levels': self.org_levels,
            'faceted': self.faceted,
            'created': self.created,
            'updated': self.updated,
        }

    def __repr__(self):
        return '<Metric %r >' % (self.name)
