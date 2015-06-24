import logging

from flask import Blueprint

from newslynx.views.decorators import load_user, load_org
from newslynx.exc import NotFoundError, RequestError
from newslynx.models import ContentItem
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data, url_for_job_status
from newslynx.tasks import ingest_bulk
from newslynx.tasks import ingest_metric
from newslynx.tasks.query_metric import ContentMetricTimeseries
from newslynx.views.util import (
    arg_bool, arg_str, validate_ts_unit, arg_list,
    arg_date, arg_int
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

    # select / exclude
    select, exclude = arg_list('select', typ=str, exclusions=True, default=['*'])
    if '*' in select:
        exclude = []
        select = "*"

    kw = dict(
        unit=arg_str('unit', default='hour'),
        sparse=arg_bool('sparse', default=True),
        sig_digits=arg_int('sig_digits', default=2),
        select=select,
        exclude=exclude,
        rm_nulls=arg_bool('rm_nulls', default=False),
        time_since_start=arg_bool('time_since_start', default=False),
        transform=arg_str('transform', default=None),
        before=arg_date('before', default=None),
        after=arg_date('after', default=None)
    )

    q = ContentMetricTimeseries(org, [content_item_id], **kw)
    return jsonify(list(q.execute()))


@bp.route('/api/v1/content/<content_item_id>/timeseries', methods=['POST'])
@load_user
@load_org
def create_content_item_timeseries(user, org, content_item_id):
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

    # check for valid format.
    if not isinstance(req_data, dict):
        raise RequestError(
            "Non-bulk endpoints require a single json object."
        )

    # insert content item id
    req_data['content_item_id'] = content_item_id

    ret = ingest_metric.content_timeseries(
        req_data,
        org_id=org.id,
        metrics_lookup=org.contet,
        commit=True)
    return jsonify(ret)


@bp.route('/api/v1/content/timeseries/bulk', methods=['POST'])
@load_user
@load_org
def bulk_create_content_timeseries(user, org):
    """
    bulk upsert timseries metrics for an organization's content items.
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
            'You must pass in a content_item_id with each record.'
        )

    job_id = ingest_bulk.content_timeseries(
        req_data,
        org_id=org.id,
        metrics_lookup=org.metrics_lookup,
        content_item_ids=org.content_item_ids,
        commit=False)
    ret = url_for_job_status(apikey=user.apikey, job_id=job_id, queue='bulk')
    return jsonify(ret, status=202)


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

    ret = ingest_metric.content_summary(
        req_data,
        org_id=org.id,
        metrics_lookup=org.metrics_lookup,
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
            'You must pass in a content_item_id with each record.'
        )

    job_id = ingest_bulk.content_summary(
        req_data,
        org_id=org.id,
        metrics_lookup=org.metrics_lookup,
        content_item_ids=org.content_item_ids,
        commit=False)

    ret = url_for_job_status(apikey=user.apikey, job_id=job_id, queue='bulk')
    return jsonify(ret, status=202)
