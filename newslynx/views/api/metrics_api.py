from collections import defaultdict, Counter

from flask import Blueprint
from sqlalchemy import or_

from newslynx.core import db
from newslynx.models import Metric, Recipe, SousChef
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify
from newslynx.exc import RequestError, NotFoundError
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import *
from newslynx.lib.stats import parse_number

# bp
bp = Blueprint('metrics', __name__)


@bp.route('/api/v1/metrics', methods=['GET'])
@load_user
@load_org
def list_metrics(user, org):

    # optionally filter by type/level/category
    include_recipes, exclude_recipes = \
        arg_list('recipes', default=[], typ=str, exclusions=True)
    include_sous_chefs, exclude_sous_chefs = \
        arg_list('sous_chefs', default=[], typ=str, exclusions=True)
    include_levels, exclude_levels = \
        arg_list('levels', default=[], typ=str, exclusions=True)
    include_aggregations, exclude_aggregations = \
        arg_list('aggregations', default=[], typ=str, exclusions=True)
    cumulative = arg_bool('cumulative', default=None)
    faceted = arg_bool('faceted', default=None)
    timeseries = arg_bool('timeseries', default=None)

    # base query
    metric_query = Metric.query.join(Recipe).join(SousChef)

    # filter by recipes
    if len(include_recipes):
        slugs = []
        ids = []
        for r in include_recipes:
            try:
                i = parse_number(r)
                ids.append(i)
            except:
                slugs.append(r)

        metric_query = metric_query\
            .filter(or_(Recipe.id.in_(ids), Recipe.slug.in_(slugs)))

    if len(exclude_recipes):
        slugs = []
        ids = []
        for r in exclude_recipes:
            try:
                i = parse_number(r)
                ids.append(i)
            except:
                slugs.append(r)

        metric_query = metric_query\
            .filter(~or_(Recipe.id.in_(ids), Recipe.slug.in_(slugs)))

    # filter by sous-chefs
    if len(include_sous_chefs):
        slugs = []
        ids = []
        for r in include_sous_chefs:
            try:
                i = parse_number(r)
                ids.append(i)
            except:
                slugs.append(r)

        metric_query = metric_query\
            .filter(or_(SousChef.id.in_(ids), SousChef.slug.in_(slugs)))

    if len(exclude_sous_chefs):
        slugs = []
        ids = []
        for r in exclude_sous_chefs:
            try:
                i = parse_number(r)
                ids.append(i)
            except:
                slugs.append(r)

        metric_query = metric_query\
            .filter(~or_(SousChef.id.in_(ids), SousChef.slug.in_(slugs)))

    # filter by levels
    if len(include_levels):
        print include_levels
        validate_metric_levels(include_levels)
        metric_query = metric_query\
            .filter(Metric.level.in_(include_levels))

    if len(exclude_levels):
        validate_metric_levels(exclude_levels)
        metric_query = metric_query\
            .filter(~Metric.level.in_(exclude_levels))

    # filter by aggregations
    if len(include_aggregations):
        validate_metric_aggregations(include_aggregations)
        metric_query = metric_query\
            .filter(Metric.aggregation.in_(exclude_aggregations))

    if len(exclude_aggregations):
        validate_metric_aggregations(exclude_aggregations)
        metric_query = metric_query\
            .filter(~Metric.aggregation.in_(exclude_aggregations))

    # filter by cumulative
    if cumulative is not None:
        metric_query.filter(Metric.cumulative is cumulative)

    # filter by timeseries
    if timeseries is not None:
        metric_query.filter(Metric.timeseries is timeseries)

    # filter by faceted
    if faceted is not None:
        metric_query.filter(Metric.faceted is faceted)

    facets = defaultdict(Counter)
    metrics = []
    for m in metric_query.all():
        facets['timeseries'][str(m.timeseries).lower()] += 1
        facets['cumulative'][str(m.cumulative).lower()] += 1
        facets['faceted'][str(m.faceted).lower()] += 1
        facets['levels'][m.level] += 1
        facets['aggregations'][m.aggregation] += 1
        facets['recipes'][m.recipe.slug] += 1
        metrics.append(m)

    resp = {
        'metrics': metrics,
        'facets': facets
    }
    return jsonify(resp)


@bp.route('/api/v1/metrics/<name_id>', methods=['GET'])
@load_user
@load_org
def get_metric(user, org, name_id):

    m = fetch_by_id_or_field(Metric, 'name', name_id, org_id=org.id)
    if not m:
        raise NotFoundError(
            'Metric "{}" does not yet exist for Org "{}"'
            .format(name_id, org.name))

    return jsonify(m)


@bp.route('/api/v1/metrics/<name_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_metric(user, org, name_id):

    m = fetch_by_id_or_field(Metric, 'name', name_id, org_id=org.id)
    if not m:
        raise NotFoundError(
            'Metric "{}" does not yet exist for Org "{}"'
            .format(name_id, org.name))

    # get the request data
    req_data = request_data()

    pass


@bp.route('/api/v1/metrics/<name_id>', methods=['DELETE'])
@load_user
@load_org
def delete_metric(user, org, name_id):

    m = fetch_by_id_or_field(Metric, 'name', name_id, org_id=org.id)
    if not m:
        raise NotFoundError(
            'Metric "{}" does not yet exist for Org "{}"'
            .format(name_id, org.name))

    if m.level == 'content_item':
        cmd = """
            UPDATE content_metric_timseries SET metrics=json_delete_keys(metrics, '{name}';
            UPDATE content_metric_summary SET metrics=json_delete_keys(metrics, '{name}';
        """.format(name=m.name)

    if m.level == 'org':
        cmd = """
            UPDATE org_metric_timeseries SET metrics=json_delete_keys(metrics, '{name}';
            UPDATE org_metric_summary SET metrics=json_delete_keys(metrics, '{name}';
        """.format(name=m.name)

    if m.level == 'all':
        cmd = """
            UPDATE content_metric_timseries SET metrics=json_delete_keys(metrics, '{name}';
            UPDATE content_metric_summary SET metrics=json_delete_keys(metrics, '{name}';
            UPDATE org_metric_timeseries SET metrics=json_delete_keys(metrics, '{name}';
            UPDATE org_metric_summary SET metrics=json_delete_keys(metrics, '{name}';
        """.format(name=m.name)

    db.session.delete(m)
    db.session.execute(cmd)
    db.session.commit()

    return delete_response()
