import logging

from flask import Blueprint

from newslynx.views.decorators import load_user, load_org
from newslynx.exc import NotFoundError, RequestError
from newslynx.models import ContentItem
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data, url_for_job_status
from newslynx.tasks import load
from newslynx.tasks import rollup_metric
from newslynx.views.util import arg_int


# blueprint
bp = Blueprint('content_summary', __name__)

log = logging.getLogger(__name__)


@bp.route('/api/v1/content/<content_item_id>/summary', methods=['POST'])
@load_user
@load_org
def content_metrics_summary(user, org, content_item_id):
    """
    upsert summary metrics for a content_item.
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

    # check for valid format.
    if not isinstance(req_data, dict):
        raise RequestError(
            "Non-bulk endpoints require a single json object."
        )

    # insert content item id
    req_data['content_item_id'] = content_item_id

    ret = load.content_summary(
        req_data,
        org_id=org.id,
        metrics_lookup=org.content_summary_metrics,
        content_item_ids=org.content_item_ids,
        commit=True
    )
    return jsonify(ret)


@bp.route('/api/v1/content/summary/bulk', methods=['POST'])
@load_user
@load_org
def bulk_create_content_summary(user, org):
    """
    bulk upsert summary metrics for an organization's content items.
    """
    req_data = request_data()

    # check for valid format.
    if not isinstance(req_data, list):
        raise RequestError(
            "Bulk endpoints require a list of json objects."
        )

    # check for content_item_id.
    if not 'content_item_id' in req_data[0].keys():
        raise RequestError(
            'You must pass in a content_item_id with each record.')

    job_id = load.content_summary(
        req_data,
        org_id=org.id,
        metrics_lookup=org.content_summary_metrics,
        content_item_ids=org.content_item_ids,
        commit=False)

    ret = url_for_job_status(apikey=user.apikey, job_id=job_id, queue='bulk')
    return jsonify(ret, status=202)


@bp.route('/api/v1/content/summary', methods=['PUT'])
@load_user
@load_org
def refresh_content_summary(user, org):
    """
    Refresh content summary metrics
    """
    # how many hours since last update should we refresh?
    since = arg_int('since', 24)

    # rollup timeseries => summary
    rollup_metric.content_summary(org, [], since)

    # simple response
    return jsonify({'success': True})


@bp.route('/api/v1/content/<content_item_id>/summary', methods=['PUT'])
@load_user
@load_org
def refresh_one_content_summary(user, org, content_item_id):
    """
    Refresh content summary metrics
    """
    since = arg_int('since', 24)
    rollup_metric.content_timeseries_to_summary(org, [content_item_id], since)
    rollup_metric.event_tags_to_summary(org, [content_item_id])
    return jsonify({'success': True})
