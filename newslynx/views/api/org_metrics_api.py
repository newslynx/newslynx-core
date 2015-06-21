import logging

from flask import Blueprint

from newslynx.views.decorators import load_user, load_org
from newslynx.exc import RequestError, NotFoundError
from newslynx.models import Org
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data
from newslynx.tasks import ingest_metric
from newslynx.tasks import query_metric
from newslynx.models.util import fetch_by_id_or_field
from newslynx.views.util import (
    arg_bool, arg_str, validate_ts_unit, localize
)

# blueprint
bp = Blueprint('org_metrics', __name__)

log = logging.getLogger(__name__)


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

    # localize
    localize(org)

    unit = arg_str('unit', default='hour')
    sparse = arg_bool('sparse', default=True)
    cumulative = arg_bool('cumulative', default=False)

    validate_ts_unit(unit)

    # execute query
    ts = query_metric.org_ts(
        org,
        unit=unit,
        sparse=sparse,
        cumulative=cumulative)

    return jsonify(ts)


@bp.route('/api/v1/orgs/<org_id_slug>/timeseries', methods=['POST'])
@load_user
@load_org
def org_metrics_timeseries(user, org_id_slug):

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

    ret = ingest_metric.org_timeseries(
        req_data,
        org.id,
        org.metrics_lookup
    )
    return jsonify(ret)


@bp.route('/api/v1/orgs/<org_id_slug>/summary', methods=['POST'])
@load_user
@load_org
def org_metrics_summary(user, org_id_slug):

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

    ret = ingest_metric.org_summary(
        req_data,
        org.id,
        org.metrics_lookup
    )
    return jsonify(ret)
