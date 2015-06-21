import logging

from flask import Blueprint

from newslynx.views.decorators import load_user, load_org
from newslynx.exc import NotFoundError
from newslynx.models import ContentItem
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data
from newslynx.tasks import ingest_metric
from newslynx.tasks import query_metric
from newslynx.views.util import (
    arg_bool, arg_str, validate_ts_unit
)

# blueprint
bp = Blueprint('content_metrics', __name__)

log = logging.getLogger(__name__)


@bp.route('/api/v1/content/<content_item_id>/timeseries', methods=['GET'])
@load_user
@load_org
def get_content_timeseries(user, org, content_item_id):
    """
    Query an individual content timeseries.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id)\
        .filter_by(org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'A ContentItem with ID {} does not exist'
            .format(content_item_id))

    unit = arg_str('unit', default='hour')
    sparse = arg_bool('sparse', default=True)
    cumulative = arg_bool('cumulative', default=False)

    validate_ts_unit(unit)

    # execute query
    ts = query_metric.content_item_ts(
        org,
        content_item_id,
        unit=unit,
        sparse=sparse,
        cumulative=cumulative)

    return jsonify(ts)


@bp.route('/api/v1/content/<content_item_id>/timeseries', methods=['POST'])
@load_user
@load_org
def create_content_timeseries(user, org, content_item_id):
    """
    Upsert content timseries metrics.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id)\
        .filter_by(org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'A ContentItem with ID {} does not exist'
            .format(content_item_id))
    req_data = request_data()

    ret = ingest_metric.content_timeseries(
        req_data,
        content_item_id=content_item_id,
        org=org)

    return jsonify(ret)


@bp.route('/api/v1/content/<content_item_id>/summary', methods=['POST'])
@load_user
@load_org
def content_metrics_summary(user, org, content_item_id):
    c = ContentItem.query\
        .filter_by(id=content_item_id)\
        .filter_by(org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'A ContentItem with ID {} does not exist'
            .format(content_item_id))
    req_data = request_data()

    ret = ingest_metric.content_summary(
        req_data,
        content_item_id,
        org.id,
        org.metrics_lookup
    )
    return jsonify(ret)
