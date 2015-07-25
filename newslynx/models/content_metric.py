from sqlalchemy.dialects.postgresql import JSON

from newslynx.lib import dates
from newslynx.core import db


class ContentMetricTimeseries(db.Model):

    """
    A content-metric is a no-sql store of org_id's, content_item_id's, datetimes (optional), and json metrics.

    """
    __tablename__ = 'content_metric_timeseries'
    __module__ = 'newslynx.models.content_metric'

    # the ID is the global bitly hash.
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True, primary_key=True)
    content_item_id = db.Column(db.Integer, db.ForeignKey('content.id'), index=True, primary_key=True)
    datetime = db.Column(db.DateTime(timezone=True), primary_key=True)
    metrics = db.Column(JSON)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.content_item_id = kw.get('content_item_id')
        self.datetime = kw.get('datetime')
        self.metrics = kw.get('metrics', {})

    def to_dict(self):
        return {
            'org_id': self.org_id,
            'content_item_id': self.content_item_id,
            'datetime': self.datetime,
            'metrics': self.metrics
        }

    def __repr__(self):
        return '<ContentTimeseriesMetric %r /  %r >' % (self.content_item_id, self.datetime)


class ContentMetricSummary(db.Model):

    """
    A content-metric is a no-sql store of org_id's, content_item_id's, datetimes (optional), and json metrics.

    """
    __tablename__ = 'content_metric_summary'
    __module__ = 'newslynx.models.content_metric'

    # the ID is the global bitly hash.
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True, primary_key=True)
    content_item_id = db.Column(db.Integer, db.ForeignKey('content.id'), index=True, primary_key=True)
    metrics = db.Column(JSON)

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.content_item_id = kw.get('content_item_id')
        self.metrics = kw.get('metrics', {})

    def to_dict(self):
        return {
            'org_id': self.org_id,
            'content_item_id': self.content_item_id,
            'metrics': self.metrics
        }

    def __repr__(self):
        return '<ContentMetricSummary %r >' % (self.content_item_id)
