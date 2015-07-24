from sqlalchemy.dialects.postgresql import ENUM, ARRAY

from newslynx.core import db
from newslynx.lib import dates
from newslynx.models import computed_metric_schema
from newslynx.constants import (
    METRIC_TYPES, METRIC_AGGS
)

# a lookup of metric type to postgresql aggregation function
TYPE_TO_AGG_FX = {
    "count": "sum",
    "cumulative": "sum",
    "percentile": "avg",
    "median": "median",
    "average": "avg",
    "min_rank": "min",
    "max_rank": "max",
    "computed": "avg"
}


class Metric(db.Model):

    """
    A metric is a concept created by a recipe and (ultimately) associated with
    an org or an org and a content-item.

    Metrics are primarily created in SousChef configurations.
    For instance, the Google Analytics Sous Chef will
    specify metadata about pageviews / time on page / entrances / exits / etc.

    When a recipe associated with this sous chef is created, records for each
    of these metrics will be inserted into this table.

    ## TODO:
    Computed metrics are formulas of existing metrics. For a computed metric to be
    valid it's associated metrics must exist on the same level.

    You cannot compute metrics from computed metrics.
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
    description = db.Column(db.Text)
    type = db.Column(ENUM(*METRIC_TYPES, name='metric_types_enum'), index=True)
    agg = db.Column(ENUM(*METRIC_AGGS, name='metric_aggs_enum'), index=True)
    content_levels = db.Column(ARRAY(db.Text), index=True)
    org_levels = db.Column(ARRAY(db.Text), index=True)
    faceted = db.Column(db.Boolean, index=True, default=False)
    computed = db.Column(db.Boolean, index=True, default=False)
    formula = db.Column(db.Text)
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(
        db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    __table_args__ = (
        db.UniqueConstraint('org_id', 'name', 'type'),
    )

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.recipe_id = kw.get('recipe_id')
        self.name = kw.get('name')
        self.description = kw.get('description')
        self.display_name = kw.get('display_name')
        self.type = kw.get('type')
        self.agg = kw.get('agg', TYPE_TO_AGG_FX.get(kw.get('type')))
        self.content_levels = kw.get('content_levels', [])
        self.org_levels = kw.get('org_levels', [])
        self.faceted = kw.get('faceted', False)
        self.formula = kw.get('formula')

    @property
    def computed(self):
        return self.type == 'computed'

    @property
    def formula_requires(self):
        return computed_metric_schema.required_metrics(self.formula)

    def to_dict(self):
        d = {
            'id': self.id,
            'org_id': self.org_id,
            'recipe_id': self.recipe_id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'type': self.type,
            'agg': self.agg,
            'content_levels': self.content_levels,
            'org_levels': self.org_levels,
            'faceted': self.faceted,
            'created': self.created,
            'updated': self.updated
        }
        if self.computed:
            d['formula'] = self.formula
            d['formula_requires'] = self.formula_requires
        return d

    def __repr__(self):
        return '<Metric %r >' % (self.name)
