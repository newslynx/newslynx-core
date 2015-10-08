import logging

from flask import Blueprint

from newslynx.views.decorators import load_user
from newslynx.exc import NotFoundError, ForbiddenError
from newslynx.models import Org
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data
from newslynx.tasks import load
from newslynx.tasks.query_metric import QueryOrgMetricTimeseries
from newslynx.tasks import rollup_metric
from newslynx.tasks import compute_metric
from newslynx.models.util import fetch_by_id_or_field
from newslynx.views.util import (
    arg_bool, arg_str, localize,
    url_for_job_status,  arg_list, arg_date, arg_int,
    request_ts)

# blueprint
bp = Blueprint('org_metrics', __name__)

log = logging.getLogger(__name__)


@bp.route('/api/v1/org/<org_id_slug>/summary', methods=['GET'])
@load_user
def get_org_summary(user, org_id_slug):

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id_slug)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    # localize
    localize(org)

    return jsonify(org.summary_metrics)


@bp.route('/api/v1/orgs/<org_id_slug>/summary', methods=['POST'])
@load_user
def create_org_metrics_summary(user, org_id_slug):

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id_slug)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    # localize
    localize(org)

    req_data = request_data()

    ret = load.org_summary(
        req_data,
        org_id=org.id,
        mertrics_lookup=org.summary_metrics,
        queue=False
    )
    return jsonify(ret)


@bp.route('/api/v1/org/<org_id_slug>/timeseries', methods=['GET'])
@load_user
def get_org_timeseries(user, org_id_slug):

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id_slug)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    kw = request_ts()
    q = QueryOrgMetricTimeseries(org, [org.id], **kw)
    return jsonify(list(q.execute()))


@bp.route('/api/v1/orgs/<org_id_slug>/timeseries', methods=['POST'])
@load_user
def create_org_timeseries(user, org_id_slug):

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id_slug)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    # localize
    localize(org)

    req_data = request_data()

    ret = load.org_timeseries(
        req_data,
        org_id=org.id,
        metrics_lookup=org.timeseries_metrics,
        queued=False,
        commit=True
    )
    return jsonify(ret)


@bp.route('/api/v1/orgs/<org_id_slug>/timeseries/bulk', methods=['POST'])
@load_user
def bulk_create_org_timeseries(user, org_id_slug):

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id_slug)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    req_data = request_data()

    job_id = load.org_timeseries(
        req_data,
        org_id=org.id,
        metrics_lookup=org.timeseries_metrics,
        queued=True
    )
    ret = url_for_job_status(apikey=user.apikey, job_id=job_id, queue='bulk')
    return jsonify(ret)


@bp.route('/api/v1/org/<org_id_slug>/timeseries', methods=['PUT'])
@load_user
def refresh_org_timeseries(user, org_id_slug):
    """
    Refresh content summary metrics
    """
    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id_slug)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    # how many hours since last update should we refresh?
    since = arg_int('since', 24)

    # rollup timeseries => summary
    rollup_metric.org_timeseries(org, [], since)

    # simple response
    return jsonify({'success': True})


@bp.route('/api/v1/org/<org_id_slug>/summary', methods=['PUT'])
@load_user
def refresh_org_summary(user, org_id_slug):
    """
    Refresh content summary metrics
    """
    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id_slug)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    # rollup timeseries => summary
    rollup_metric.org_summary(org)

    # compute metrics
    compute_metric.org_summary(org)

    # simple response
    return jsonify({'success': True})
