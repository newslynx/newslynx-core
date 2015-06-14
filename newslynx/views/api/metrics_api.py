from gevent.pool import Pool

import copy
import logging

from flask import Blueprint

from newslynx.core import db
from newslynx.views.decorators import load_user, load_org
from newslynx.exc import RequestError, NotFoundError
from newslynx.models import ContentItem
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data
from newslynx.tasks.ingest_metric import *

# blueprint
bp = Blueprint('metrics', __name__)

log = logging.getLogger(__name__)


@bp.route('/api/v1/content/<content_item_id>/timeseries', methods=['POST'])
@load_user
@load_org
def content_metrics_timeseries(user, org, content_item_id):
    c = ContentItem.query.get(content_item_id)
    if not c:
        raise NotFoundError(
            'A ContentItem with ID {} does not exist'
            .format(content_item_id))
    req_data = request_data()

    ret = ingest_content_metric_timeseries(
        req_data,
        content_item_id,
        org.id,
        org.metrics_lookup
    )
    return jsonify(ret)


@bp.route('/api/v1/content/<content_item_id>/summary', methods=['POST'])
@load_user
@load_org
def content_metrics_summary(user, org, content_item_id):
    c = ContentItem.query.get(content_item_id)
    if not c:
        raise NotFoundError(
            'A ContentItem with ID {} does not exist'
            .format(content_item_id))
    req_data = request_data()

    ret = ingest_content_metric_summary(
        req_data,
        content_item_id,
        org.id,
        org.metrics_lookup
    )
    return jsonify(ret)


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

    ret = ingest_org_metric_timeseries(
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

    ret = ingest_org_metric_summary(
        req_data,
        org.id,
        org.metrics_lookup
    )
    return jsonify(ret)
