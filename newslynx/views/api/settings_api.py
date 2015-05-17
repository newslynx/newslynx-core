from flask import Blueprint

from newslynx.core import db
from newslynx.models import Setting
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify, json_to_obj
from newslynx.exc import RequestError, NotFoundError
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import (
    request_data, BOOL_TRUISH, delete_response)

# bp
bp = Blueprint('settings', __name__)


@bp.route('/api/v1/settings', methods=['GET'])
@load_user
@load_org
def org_settings(user, org):

    return jsonify(org.settings)


@bp.route('/api/v1/settings', methods=['POST'])
@load_user
@load_org
def create_setting(user, org):

    # get the request data
    req_data = request_data()

    name = req_data.get('name')
    value = req_data.get('value')
    json_value = req_data.get('json_value')

    if not name or not value:
        raise RequestError(
            "You must pass in a 'name' and 'value' to create a setting. "
            "You only passed in: {}".format(", ".join(req_data.keys())))

    # if it's a json_value check whether we can parse it as such
    if json_value:
        if isinstance(value, basestring):
            try:
                json_to_obj(value)
            except:
                raise RequestError(
                    "Setting '{}' with value '{}' was declared as a "
                    "'json_value' but could not be parsed as such."
                    .format(name, value))

    s = Setting(
        org_id=org.id,
        name=name,
        value=value,
        json_value=json_value or False)

    db.session.add(s)

    # no duplicates.
    try:
        db.session.commit()
    except Exception as e:
        raise RequestError(e.message)

    return jsonify(s)


@bp.route('/api/v1/settings/<name>', methods=['GET'])
@load_user
@load_org
def get_setting(user, org, name):

    s = fetch_by_id_or_field(Setting, 'name', name, org_id=org.id)
    if not s:
        raise NotFoundError('Setting "{}" does not yet exist for Org "{}"'
                            .format(name, org.name))
    return jsonify(s)


@bp.route('/api/v1/settings/<name>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_setting(user, org, name):

    s = fetch_by_id_or_field(Setting, 'name', name, org_id=org.id)

    if not s:
        raise NotFoundError('Setting "{}" does not yet exist for Org "{}"'
                            .format(name, org.name))

    # get the request data
    req_data = request_data()

    name = req_data.get('name')
    value = req_data.get('value')
    json_value = req_data.get('json_value')

    # if it's a json_value check whether we can parse it as such
    if json_value:
        if isinstance(value, basestring):
            try:
                json_to_obj(value)
            except:
                raise RequestError(
                    "Setting '{}' with value '{}' was declared as a "
                    "'json_value' but could not be parsed as such."
                    .format(name, value))

    # upsert / patch values.
    if name:
        s.name = name

    if value:
        s.value = value

    if json_value:
        if not isinstance(json_value, bool):
            if str(json_value) in BOOL_TRUISH:
                json_value = True
            else:
                json_value = False
        s.json_value = json_value

    db.session.add(s)
    db.session.commit()

    return jsonify(s)


@bp.route('/api/v1/settings/<name>', methods=['DELETE'])
@load_user
@load_org
def delete_setting(user, org, name):

    s = fetch_by_id_or_field(Setting, 'name', name, org_id=org.id)

    if not s:
        raise NotFoundError('Setting "{}" does not yet exist for Org "{}"'
                            .format(name, org.name))

    db.session.delete(s)
    db.session.commit()

    return delete_response()
