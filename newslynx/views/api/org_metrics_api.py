import logging

from flask import Blueprint, request

from newslynx.views.decorators import load_user
from newslynx.exc import NotFoundError, ForbiddenError
from newslynx.models import Org
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data
from newslynx.tasks import load
from newslynx.tasks.query_metric import QueryOrgMetricTimeseries
from newslynx.models.util import fetch_by_id_or_field
from newslynx.views.util import (
    arg_bool, arg_str, validate_ts_unit, localize,
    url_for_job_status,  arg_list, arg_date, arg_int)

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

    # todo: validate which metrics you can select.

    # select / exclude
    select, exclude = arg_list(
        'select', typ=str, exclusions=True, default=['*'])
    if '*' in select:
        exclude = []
        select = "*"

    kw = dict(
        unit=arg_str('unit', default='hour'),
        sparse=arg_bool('sparse', default=True),
        sig_digits=arg_int('sig_digits', default=2),
        select=select,
        exclude=exclude,
        group_by_id=arg_bool('group_by_id', default=True),
        rm_nulls=arg_bool('rm_nulls', default=False),
        time_since_start=arg_bool('time_since_start', default=False),
        transform=arg_str('transform', default=None),
        before=arg_date('before', default=None),
        after=arg_date('after', default=None)
    )

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
