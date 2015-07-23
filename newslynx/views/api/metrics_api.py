from collections import defaultdict, Counter

from flask import Blueprint
from sqlalchemy import or_

from newslynx.core import db
from newslynx.models import Metric, Recipe, SousChef
from newslynx.models.util import (
    fetch_by_id_or_field, get_table_columns)
from newslynx.lib.serialize import jsonify
from newslynx.exc import NotFoundError, RequestError
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
    include_types, exclude_types = \
        arg_list('types', default=[], typ=str, exclusions=True)
    include_content_levels, exclude_content_levels = \
        arg_list('content_levels', default=[], typ=str, exclusions=True)
    include_org_levels, exclude_org_levels = \
        arg_list('org_levels', default=[], typ=str, exclusions=True)
    sort_field, direction = arg_sort('sort', default='display_name')
    faceted = arg_bool('faceted', default=None)
    computed = arg_bool('computed', default=None)

    # base query
    metric_query = Metric.query.join(Recipe).join(SousChef)

    # validate sort fields are part of Recipe object.
    if sort_field:
        validate_fields(Metric, fields=[sort_field], suffix='to sort by')

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
    if len(include_types):
        metric_query = metric_query\
            .filter(Metric.type.in_(include_types))

    if len(exclude_types):
        metric_query = metric_query\
            .filter(~Metric.type.in_(exclude_types))

    # filter by levels
    if len(include_content_levels):
        metric_query = metric_query\
            .filter(Metric.content_levels.contains(include_content_levels))

    if len(exclude_content_levels):
        metric_query = metric_query\
            .filter(~Metric.content_levels.contains(exclude_content_levels))

    if len(include_org_levels):
        metric_query = metric_query\
            .filter(Metric.org_levels.contains(include_org_levels))

    if len(exclude_org_levels):
        metric_query = metric_query\
            .filter(~Metric.org_levels.contains(exclude_org_levels))

    # filter by faceted
    if faceted is not None:
        metric_query = metric_query\
            .filter(Metric.faceted == faceted)

    if computed is not None:
        metric_query = metric_query\
            .filter(Metric.computed == computed)

    if sort_field:
        sort_obj = eval('Metric.{}.{}'.format(sort_field, direction))
        metric_query = metric_query.order_by(sort_obj())

    facets = defaultdict(Counter)

    metrics = []

    for m in metric_query.all():
        facets['recipes'][m.recipe.slug] += 1
        facets['types'][m.type] += 1
        if 'faceted' in facets:
            if m.faceted:
                facets['faceted'] += 1
        else:
            facets['faceted'] = 0
        if 'computed' in facets:
            if m.computed:
                facets['computed'] += 1
        else:
            facets['computed'] = 0
        for cl in m.content_levels:
            facets['content_levels'][cl] += 1
        for cl in m.org_levels:
            facets['org_levels'][cl] += 1

        metrics.append(m.to_dict())

    resp = {
        'metrics': metrics,
        'facets': facets
    }
    return jsonify(resp)


@bp.route('/api/v1/metrics', methods=['POST'])
@load_user
@load_org
def create_computed_metric(user, org):
    """
    TODO: allow for creation of arbitrary computed metrics here.
    """
    raise NotImplementedError(
        "Creation of new metrics is limited to Sous Chefs / Recipes.")


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


@bp.route('/api/v1/metrics/content-timeseries', methods=['GET'])
@load_user
@load_org
def get_content_timeseries_metrics(user, org):
    return jsonify(org.content_timeseries_metrics.values())


@bp.route('/api/v1/metrics/content-timeseries/computed', methods=['GET'])
@load_user
@load_org
def get_computed_content_timeseries_metrics(user, org):
    return jsonify(org.computed_timeseries_metrics.values())


@bp.route('/api/v1/metric/content-summary', methods=['GET'])
@load_user
@load_org
def get_content_summary_metrics(user, org):
    return jsonify(org.content_summary_metrics.values())


@bp.route('/api/v1/metrics/content-summary-sort', methods=['GET'])
@load_user
@load_org
def get_content_summary_metric_sorts(user, org):
    return jsonify(org.content_summary_metric_sorts.values())


@bp.route('/api/v1/metrics/content-summary/computed', methods=['GET'])
@load_user
@load_org
def get_computed_content_summary_metrics(user, org):
    return jsonify(org.computed_content_summary_metrics.values())


@bp.route('/api/v1/metrics/content-comparison', methods=['GET'])
@load_user
@load_org
def get_content_comparsion_metrics(user, org):
    return jsonify(org.content_comparsion_metrics.values())


@bp.route('/api/v1/metrics/org-timeseries', methods=['GET'])
@load_user
@load_org
def get_org_timeseries_metrics(user, org):
    return jsonify(org.timeseries_metrics.values())


@bp.route('/api/v1/metrics/org-timeseries/computed', methods=['GET'])
@load_user
@load_org
def get_computed_org_timeseries_metrics(user, org):
    return jsonify(org.computed_timeseries_metrics.values())


@bp.route('/api/v1/metrics/org-summary', methods=['GET'])
@load_user
@load_org
def get_org_summary_metrics(user, org):
    return jsonify(org.summary_metrics.values())


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

    # filter out any non-columns
    columns = get_table_columns(Metric)
    for k in req_data.keys():
        if k not in columns:
            req_data.pop(k)

    # don't ever overwrite these:
    for k in ['id', 'recipe_id', 'name', 'org_id', 'created', 'updated']:
        if k in req_data:
            req_data.pop(k, None)

    # update fields
    for k, v in req_data.items():
        setattr(m, k, v)
    try:
        db.session.add(m)
        db.session.commit()
    except Exception as e:
        raise RequestError("Error updating Metric: {}".format(e.message))

    return jsonify(m)


@bp.route('/api/v1/metrics/<name_id>', methods=['DELETE'])
@load_user
@load_org
def delete_metric(user, org, name_id):

    m = fetch_by_id_or_field(Metric, 'name', name_id, org_id=org.id)
    if not m:
        raise NotFoundError(
            'Metric "{}" does not yet exist.'
            .format(name_id))

    # format for deleting metrics from metric store.
    cmd_fmt = "UPDATE {table} " + \
              "SET metrics=json_del_keys(metrics, '{name}'::text);"\
              .format(name=m.name)

    # delete metric from metric stores.
    if 'timeseries' in m.content_levels:
        db.session.execute(cmd_fmt.format(table="content_metric_timeseries"))

    if 'summary' in m.content_levels:
        db.session.execute(cmd_fmt.format(table="content_metric_summary"))

    if 'timeseries' in m.org_levels:
        db.session.execute(cmd_fmt.format(table="org_metric_timeseries"))

    if 'summary' in m.org_levels:
        db.session.execute(cmd_fmt.format(table="org_metric_summary"))

    db.session.delete(m)
    db.session.commit()

    return delete_response()
