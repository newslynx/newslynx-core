from sqlalchemy.dialects.postgresql import ENUM

from newslynx.core import db
from newslynx.lib import dates
from newslynx.taxonomy import METRIC_CATEGORIES


class Metric(db.Model):

    """
    A metric is a long data structure of key/value timeseries stats.

    A metric follows this taxonomy:

    category:

        - promotion (i.e. time spent on homepage)
        - performance (i.e.  pageviews, tweets)
        - impact (i.e. number of impact events)

    level:
        - thing
        - organization

    faceted metrics can be represented with the following naming convention:
    {facet_name}__{facet_value}
    """

    __tablename__ = 'metrics'

    id = db.Column(db.Integer, unique=True, primary_key=True, index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), index=True
    )
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), index=True)
    thing_id = db.Column(db.Integer, db.ForeignKey('things.id'), index=True)
    name = db.Column(db.Text, index=True)
    value = db.Column(db.Float, index=True)
    category = db.Column(
        ENUM(*METRIC_CATEGORIES, name='metric_categories_enum'), index=True)
    level = db.Column(
        ENUM('thing', 'organization', name='metric_levels_enum'), index=True)
    cumulative = db.Column(db.Boolean, index=True)
    timeseries = db.Column(db.Boolean, index=True)
    created = db.Column(db.DateTime(timezone=True), index=True)

    __table_args__ = (
        db.UniqueConstraint(
            'thing_id', 'organization_id', 'recipe_id', 'name', 'created'),
    )

    def __init__(self, **kw):
        self.organization_id = kw.get('organization_id')
        self.recipe_id = kw.get('recipe_id')
        self.thing_id = kw.get('thing_id')
        self.name = kw.get('name')
        self.value = kw.get('value')
        self.created = kw.get('created', dates.now())
        self.category = kw.get('category')
        self.level = kw.get('level')
        self.cumulative = kw.get('cumulative')
        self.timeseries = kw.get('timeseries')
        self.meta = kw.get('meta', {})

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'recipe_id': self.recipe_id,
            'thing_id': self.thing_id,
            'name': self.name,
            'value': self.value,
            'created': self.created,
            'category': self.category,
            'level': self.level,
            'cumulative': self.cumulative,
            'timeseries': self.timeseries,
            'meta': self.meta
        }

    def __repr__(self):
        return '<Metric %r / %r >' % (self.name, self.value)
