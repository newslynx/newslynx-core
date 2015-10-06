from flask import Blueprint

from newslynx.core import db
from newslynx.models import Setting
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify, json_to_obj, obj_to_json
from newslynx.exc import RequestError, NotFoundError, ConflictError
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import (
    request_data, delete_response, arg_str)
from newslynx.constants import TRUE_VALUES

# bp
bp = Blueprint('settings', __name__)


@bp.route('/api/v1/<level>/settings', methods=['GET'])
@load_user
@load_org
def list_settings(user, org, level):
    if level not in ['me', 'orgs']:
        raise NotFoundError(
            'You cannot store settings for \'{}\''
            .format(level))
    if level == 'orgs':
        return jsonify(org.settings)
    return jsonify(user.get_settings(org_id=org.id))


@bp.route('/api/v1/<level>/settings', methods=['POST'])
@load_user
@load_org
def create_setting(user, org, level):
    if level not in ['me', 'orgs']:
        raise NotFoundError(
            'You cannot store settings for \'{}\''
            .format(level))

    # get the request data
    req_data = request_data()

    name = req_data.get('name')
    value = req_data.get('value')
    json_value = req_data.get('json_value', False)

    if not name or not value:
        raise RequestError(
            "You must pass in a 'name' and 'value' to create a setting. "
            "You only passed in: {}"
            .format(", ".join(req_data.keys())))

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
        user_id=user.id,
        level=level,
        name=name,
        value=value,
        json_value=json_value or False)

    db.session.add(s)

    # no duplicates.
    try:
        db.session.commit()
    except Exception as e:
        raise ConflictError(e.message)

    # temporary hack for 'timezone' setting in the APP.
    if 'name' == 'timezone' and level == 'orgs':
        org.timezone = value

        try:
            db.session.add(org)
            db.session.commit()
        except Exception as e:
            raise RequestError(
                "An error occurred while updating the timezone. "
                "Here's the error message: {}"
                .format(org.name, e.message))
    return jsonify(s)


@bp.route('/api/v1/<level>/settings/<name_id>', methods=['GET'])
@load_user
@load_org
def get_setting(user, org, level, name_id):

    if level not in ['me', 'orgs']:
        raise NotFoundError(
            'You cannot store settings for \'{}\''
            .format(level))
    if level == 'me':
        s = fetch_by_id_or_field(
            Setting, 'name', name_id, org_id=org.id, user_id=user.id, level=level)
    else:
        s = fetch_by_id_or_field(
                Setting, 'name', name_id, org_id=org.id, level=level)
    if not s:
        raise NotFoundError(
            'Setting "{}" does not yet exist for Org "{}"'
            .format(name_id, org.name))

    return jsonify(s)


@bp.route('/api/v1/<level>/settings/<name_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_setting(user, org, level, name_id):

    if level not in ['me', 'orgs']:
        raise NotFoundError(
            'You cannot store settings for \'{}\''
            .format(level))

    s = fetch_by_id_or_field(
        Setting, 'name', name_id, org_id=org.id, user_id=user.id, level=level)

    if not s:
        raise NotFoundError(
            'Setting "{}" does not yet exist.'
            .format(name_id, org.name))

    # get the request data
    req_data = request_data()

    name = req_data.get('name')
    value = req_data.get('value')
    json_value = req_data.get('json_value')

    # if it's a json_value check whether we can parse it as such
    if json_value:
        if isinstance(value, basestring):
            try:
                obj_to_json(value)
            except:
                raise RequestError(
                    "Setting '{}' with value '{}' was declared as a "
                    "'json_value' but could not be parsed as such."
                    .format(name_id, value))

    # upsert / patch values.
    if name:
        s.name = name

    if json_value:
        if not isinstance(json_value, bool):
            if str(json_value).lower() in TRUE_VALUES:
                json_value = True
            else:
                json_value = False
        s.json_value = json_value
        s.value = obj_to_json(value)
    else:
       s.value = value
    db.session.add(s)
    db.session.commit()

    return jsonify(s)


@bp.route('/api/v1/<level>/settings/<name_id>', methods=['DELETE'])
@load_user
@load_org
def delete_setting(user, org, level, name_id):

    if level not in ['me', 'orgs']:
        raise NotFoundError(
            'You cannot store settings for \'{}\''
            .format(level))

    s = fetch_by_id_or_field(
        Setting, 'name', name_id, org_id=org.id, user_id=user.id, level=level)

    if not s:
        raise NotFoundError(
            'Setting "{}" does not yet exist.'
            .format(name_id, org.name))

    db.session.delete(s)
    db.session.commit()

    return delete_response()
