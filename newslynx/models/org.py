import copy

from sqlalchemy import and_, or_, func
from sqlalchemy.dialects.postgresql import ENUM, ARRAY

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.serialize import json_to_obj
from newslynx.lib.text import slug
from .relations import orgs_users
from .metric import Metric
from .content_item import ContentItem


class Org(db.Model):

    __tablename__ = 'orgs'
    __module__ = 'newslynx.models.org'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    name = db.Column(db.Text, unique=True, index=True)
    slug = db.Column(db.Text, unique=True, index=True)
    timezone = db.Column(
        ENUM(*list(dates.TIMEZONES), name='org_timezones_enum'))
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(
        db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    # joins
    auths = db.relationship(
        'Auth',
        backref=db.backref('org'),
        lazy='joined',
        cascade="all, delete-orphan")
    settings = db.relationship(
        'Setting',
        backref=db.backref('org'),
        lazy='joined',
        cascade="all, delete-orphan")

    # dynamic relations
    reports = db.relationship(
        'Report',
        backref=db.backref('org'),
        lazy='dynamic',
        cascade="all, delete-orphan")
    users = db.relationship(
        'User', secondary=orgs_users,
        backref=db.backref('orgs', lazy='joined'),
        lazy='joined')
    events = db.relationship('Event', lazy='dynamic', cascade='all')
    content_items = db.relationship(
        'ContentItem', lazy='dynamic', cascade='all')
    sous_chefs = db.relationship(
        'SousChef', lazy='dynamic', cascade='all')
    metrics = db.relationship('Metric', lazy='dynamic', cascade='all')
    recipes = db.relationship(
        'Recipe', lazy='dynamic', cascade='all',
        backref=db.backref('org', lazy='joined', uselist=False))
    authors = db.relationship('Author', lazy='dynamic')
    tags = db.relationship('Tag', lazy='dynamic', cascade='all')
    timeseries = db.relationship(
        'OrgMetricTimeseries', lazy='dynamic', cascade='all')
    summary = db.relationship('OrgMetricSummary', lazy='joined', cascade='all')

    def __init__(self, **kw):
        self.name = kw.get('name')
        self.timezone = kw.get('timezone', 'UTC')
        self.slug = kw.get('slug', slug(kw['name']))

    @property
    def now(self):
        """
        The current local time for the Org.
        """
        return dates.local(self.timezone)

    @property
    def settings_dict(self):
        """
        An org's settings formatted as a dictionary.
        """
        settings = {}
        for s in self.settings:
            if s.json_value:
                v = json_to_obj(s.value)
            else:
                v = copy.copy(s.value)
            settings[s.name] = v
        return settings

    @property
    def auths_dict(self):
        """
        An org's authorizations formatted as a dictionary.
        """
        auths = {}
        for a in self.auths:
            auths[a.name] = a.value
        return auths

    @property
    def super_user(self):
        """
        Simplified access to the super user from an org object.
        """
        return [u for u in self.users if u.super_user][0]

    @property
    def user_ids(self):
        """
        An array of an org's user ids.
        """
        return [u.id for u in self.users]

    @property
    def summary_metrics(self):
        """
        Summary metrics for an organization.
        """
        return self.summary.metrics

    @property
    def domains(self):
        """
        Domains which an organization manages.
        """
        domains = db.session.query(func.distinct(ContentItem.domain))\
            .filter_by(org_id=self.id)\
            .all()
        if not domains:
            return []
        return [d[0] for d in domains if d[0] is not None]

    @property
    def content_item_ids(self):
        """
        An array of an org's content item IDs.
        """
        return [c.id for c in self.content_items]

    @property
    def simple_content_items(self):
        """
        Simplified content items.
        """
        return [
            {'id': c.id, 'url': c.url, 'type': c.type, 'title': c.title,
             'created': c.created, 'domain': c.domain}
            for c in self.content_items
        ]

    # METRICS

    ## CONTENT TIMESERIES METRICS

    @property
    def content_timeseries_metrics(self):
        """
        Content metrics that can exist in the content timeseries store.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['timeseries']))\
            .filter(Metric.type != 'computed')\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def content_timeseries_metric_names(self):
        """
        The names of metrics that can exist in the content timeseries store.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['timeseries']))\
            .filter(Metric.type != 'computed')\
            .filter(~Metric.faceted)\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    @property
    def content_timeseries_metric_rollups(self):
        """
        Content metrics that should be rolled-up from timeseries => summary.
        Computed timeseries metrics can and should be summarized for ease of
        generating comparisons on these metrics.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['timeseries', 'summary']))\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def computed_content_timeseries_metrics(self):
        """
        Metrics to compute on top of the timeseries store.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['timeseries']))\
            .filter(Metric.type == 'computed')\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    ## CONTENT SUMMARY METRICS

    @property
    def content_summary_metrics(self):
        """
        Content metrics that can exist in the content summary store.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary']))\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def content_summary_metric_names(self):
        """
        The names of metrics that can exist in the content summary store.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary']))\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    @property
    def computed_content_summary_metrics(self):
        """
        Metrics to compute on top of the content summary store.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary']))\
            .filter(~Metric.content_levels.contains(['timeseries']))\
            .filter(Metric.type == 'computed')\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def computed_content_summary_metric_names(self):
        """
        The names of metrics to compute on top of the content summary store.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary']))\
            .filter(~Metric.content_levels.contains(['timeseries']))\
            .filter(Metric.type == 'computed')\
            .filter(~Metric.faceted)\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    @property
    def computable_content_summary_metrics(self):
        """
        The names of metrics which can be used in computed summary metrics.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary']))\
            .filter(Metric.type != 'computed')\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def computable_content_summary_metrics_names(self):
        """
        The names of metrics which can be used in computed summary metrics.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary']))\
            .filter(Metric.type != 'computed')\
            .filter(~Metric.faceted)\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    @property
    def content_summary_metric_sorts(self):
        """
        The names of metrics that can can be used to sort content items.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary']))\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def content_summary_metric_sort_names(self):
        """
        The names of metrics that can can be used to sort content items.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary']))\
            .filter(~Metric.faceted)\
            .with_entities(Metric.name)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def content_metric_comparisons(self):
        """
        Content summary metrics that should be used to generate comparisons.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary', 'comparison']))\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def content_metric_comparison_names(self):
        """
        The names of content summary metrics that
        should be used to generate comparisons.
        """
        metrics = self.metrics\
            .filter(Metric.content_levels.contains(['summary', 'comparison']))\
            .filter(~Metric.faceted)\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    @property
    def content_faceted_metric_names(self):
        """
        The names of faceted content metrics.
        """
        metrics = self.metrics\
            .filter(Metric.faceted)\
            .filter(Metric.content_levels.contains(['summary']))\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    ## ORG TIMESERIES METRICS

    @property
    def timeseries_metrics(self):
        """
        Org timeseries metrics and content timeseries metrics
        which can exist in the org timeseries.

        Computed metrics should be rolled-up to the org timeseries.
        """
        metrics = self.metrics\
            .filter(
                or_(Metric.org_levels.contains(['timeseries']),
                    and_(Metric.content_levels.contains(['timeseries']),
                         Metric.org_levels.contains(['timeseries']))
                    ))\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def timeseries_metric_rollups(self):
        """
        Content metrics that should be rolled-up from timeseries => summary.
        Computed timeseries metrics can and should be summarized for ease of
        generating comparisons on these metrics.
        """
        metrics = self.metrics\
            .filter(Metric.org_levels.contains(['timeseries']))\
            .filter(Metric.content_levels.contains(['timeseries']))\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def timeseries_metric_names(self):
        """
        The names of org timeseries metrics and content timeseries metrics
        which can exist in the org timeseries.
        """
        metrics = self.metrics\
            .filter(
                or_(Metric.org_levels.contains(['timeseries']),
                    and_(Metric.content_levels.contains(['timeseries']),
                         Metric.org_levels.contains(['timeseries']))
                    ))\
            .filter(~Metric.faceted)\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    @property
    def computed_timeseries_metrics(self):
        """
        Org-specific computed timeseries metrics.
        """
        metrics = self.metrics\
            .filter(Metric.org_levels.contains(['timeseries']))\
            .filter(~Metric.content_levels.contains(['timeseries']))\
            .filter(Metric.type == 'computed')\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def computed_timeseries_metrics_names(self):
        """
        The names of metrics which can be used in computed summary metrics.
        """
        metrics = self.metrics\
            .filter(Metric.org_levels.contains(['timeseries']))\
            .filter(~Metric.content_levels.contains(['timeseries']))\
            .filter(Metric.type == 'computed')\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    @property
    def computable_timeseries_metrics(self):
        """
        Metrics which can be used in computed summary metrics.
        """
        return self.timeseries_metrics

    @property
    def computable_timeseries_metrics_names(self):
        """
        The names of metrics which can be used in computed summary metrics.
        """
        return self.timeseries_metric_names

    @property
    def summary_metrics(self):
        """
        Metrics which can exist in the org summary store.
        """
        metrics = self.metrics\
            .filter(Metric.org_levels.contains(['summary']))\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    @property
    def summary_metric_names(self):
        """
        Metrics which can exist in the org summary store.
        """
        metrics = self.metrics\
            .filter(
                or_(Metric.org_levels.contains(['summary']),
                    and_(Metric.content_levels.contains(['summary']),
                         Metric.org_levels.contains(['summary']))
                    ))\
            .filter(~Metric.faceted)\
            .with_entities(Metric.name)\
            .all()
        return [m[0] for m in metrics]

    @property
    def summary_metric_rollups(self):
        """
        Content summary metrics that should be rolled-up
        from summary =>  org summary.
        """
        metrics = self.metrics\
            .filter(Metric.org_levels.contains(['summary']))\
            .filter(Metric.content_levels.contains(['summary']))\
            .filter(~Metric.faceted)\
            .all()
        return {m.name: m.to_dict() for m in metrics}

    def to_dict(self, **kw):

        # parse kwargs
        incl_users = kw.get('incl_users', True)
        incl_domains = kw.get('incl_domains', False)
        incl_settings = kw.get('incl_settings', True)
        incl_tags = kw.get('incl_tags', False)
        incl_auths = kw.get('incl_auths', True)
        settings_as_dict = kw.get('settings_dict', True)
        auths_as_dict = kw.get('auths_dict', True)

        d = {
            'id': self.id,
            'name': self.name,
            'timezone': self.timezone,
            'slug': self.slug,
            'created': self.created,
            'updated': self.updated
        }

        if incl_users:
            d['users'] = [
                u.to_dict(incl_org=False, incl_apikey=False)
                for u in self.users
            ]

        if incl_settings:
            if settings_as_dict:
                d['settings'] = self.settings_dict

            else:
                d['settings'] = self.settings

        if incl_auths:
            if auths_as_dict:
                d['auths'] = self.auths_dict
            else:
                d['auths'] = self.auths

        if incl_tags:
            d['tags'] = [t.to_dict() for t in self.tags]

        if incl_domains:
            d['domains'] = self.domains

        return d

    def __repr__(self):
        return "<Org %s >" % (self.slug)
