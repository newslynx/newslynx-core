from flask import Blueprint

from newslynx.core import db
from newslynx.models import Metric
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify, json_to_obj
from newslynx.exc import RequestError, NotFoundError
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import (
    request_data, delete_response,
    arg_bool, arg_list)

# bp
bp = Blueprint('metrics', __name__)


@bp.route('/api/v1/metrics', methods=['GET'])
@load_user
@load_org
def list_metrics(user, org):

    metric_query = Metric.query

    return jsonify(org.settings)


@bp.route('/api/v1/metrics', methods=['POST'])
@load_user
@load_org
def create_metric(user, org):

    # TODO
    pass


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
