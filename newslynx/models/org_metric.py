from sqlalchemy.dialects.postgresql import JSON

from newslynx.lib import dates
from newslynx.core import db


class OrgMetricTimeseries(db.Model):

    """
    A org-metric is a no-sql store of org_id's datetimes (optional) and json metrics.
    """
    __tablename__ = 'org_metric_timeseries'
    __module__ = 'newslynx.models.org_metric'

    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True, primary_key=True)
    datetime = db.Column(db.DateTime(timezone=True), primary_key=True)
    metrics = db.Column(JSON)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.datetime = kw.get('datetime')
        self.metrics = kw.get('metrics', {})

    def to_dict(self):
        return {
            'org_id': self.org_id,
            'datetime': self.datetime,
            'metrics': self.metrics
        }

    def __repr__(self):
        return '<OrgMetricTimeseries %r /  %r >' % (self.org_id, self.datetime)


class OrgMetricSummary(db.Model):

    """
    A org-metric is a no-sql store of org_id's and json metrics.
    """
    __tablename__ = 'org_metric_summary'
    __module__ = 'newslynx.models.org_metric'

    # the ID is the global bitly hash.
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True, primary_key=True)
    metrics = db.Column(JSON)

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.metrics = kw.get('metrics', {})

    def to_dict(self):
        return {
            'org_id': self.org_id,
            'metrics': self.metrics
        }

    def __repr__(self):
        return '<OrgMetricSummary  %r >' % (self.org_id)
