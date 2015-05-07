from flask import Blueprint, request

from newslynx.core import db
from newslynx.models import User, Organization, Setting
from newslynx.lib.serialize import jsonify, json_to_obj
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError)
from newslynx.views.decorators import load_user
from newslynx.views.util import (
    request_data, BOOL_TRUISH, delete_response, arg_bool)

# bp
bp = Blueprint('orgs', __name__)


@bp.route('/api/v1/orgs', methods=['GET'])
@load_user
def me_orgs(user):
    return jsonify(user.organizations)


@bp.route('/api/v1/orgs', methods=['POST'])
@load_user
def org_create(user):

    req_data = request_data()

    if not user.admin:
        raise ForbiddenError(
            'You must be an admin to create or update an organization')

    org = Organization.query.filter_by(name=req_data['name']).first()

    # if the org doesnt exist, create it.
    if org:
        raise RequestError(
            "Organization '{}' already exists".format(req_data['name']))

    # add the requesting user to the org
    org = Organization(name=request.form['name'])
    org.users.append(user)
    db.session.add(org)
    db.session.commit()

    return jsonify(org)


@bp.route('/api/v1/orgs/<org_id_name>', methods=['GET'])
@load_user
def org(user, org_id_name):

  # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError('You are not allowed to access this organization')

    return jsonify(org)


@bp.route('/api/v1/orgs/<org_id_name>', methods=['PUT', 'PATCH'])
@load_user
def org_update(user, org_id_name):

    req_data = request_data()

    if not user.admin:
        raise ForbiddenError(
            'You must be an admin to create or update an organization')

  # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if the org doesnt exist, create it.
    if not org:
        raise RequestError(
            "Organization '{}' Does not exists".format(req_data['name']))

    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this organization.")

    # update the requesting user to the org
    org.name = req_data['name']
    db.session.add(org)
    db.session.commit()

    return jsonify(org)


@bp.route('/api/v1/orgs/<org_id_name>', methods=['DELETE'])
@load_user
def org_delete(user, org_id_name):

    if not user.admin:
        raise AuthError('You must be an admin to delete an Organization')

  # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError('User "{}" is not allowed to access Organization "{}".'
                             .format(user.name, org.name))

    db.session.delete(org)
    db.session.commit()

    return delete_response()


@bp.route('/api/v1/orgs/<org_id_name>/users',  methods=['GET'])
@load_user
def org_users(user, org_id_name):

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError('User "{}" is not allowed to access Organization "{}".'
                             .format(user.email, org.name))

    return jsonify(org.users)


@bp.route('/api/v1/orgs/<org_id_name>/users',  methods=['POST'])
@load_user
def org_create_user(user, org_id_name):

    if not user.admin:
        raise AuthError(
            'You must be an admin to create a user for an organization.')

    # get the form.
    req_data = request_data()
    email = req_data.get('email')
    password = req_data.get('password')
    name = req_data.get('name')
    admin = req_data.get('admin', False)
    if not isinstance(admin, bool):
        if str(admin) in BOOL_TRUISH:
            admin = True

    if not all([email, password, name]):
        raise RequestError(
            'An email, password, and name are required to create a User.')

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this organization.")

    if User.query.filter_by(email=email).first():
        raise RequestError(
            'A User with email "{}" already exists'.format(email))

    new_org_user = User(email=email, password=password, name=name, admin=admin)
    org.users.append(new_org_user)
    db.session.commit()

    return jsonify(new_org_user)


@bp.route('/api/v1/orgs/<org_id_name>/users/<user_email>',  methods=['GET'])
@load_user
def org_user(user, org_id_name, user_email):

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError('You are not allowed to access this organization')

    # get this new user by id / email

    # check for int / str
    try:
        user_email = int(user_email)
        user_str = False
    except:
        user_str = True

    if user_str:
        org_user = User.query.filter_by(email=user_email).first()
    else:
        org_user = User.query.get(user_email)

    if not org_user:
        raise RequestError('This user does not yet exist')

    # check whether this user can view this other user:
    if not len(list(set(org_user.org_ids).intersection(set(user.org_ids)))):
        raise ForbiddenError('You are not allowed to view this user.'
                             .format(user.email))

    return jsonify(org_user)


@bp.route('/api/v1/orgs/<org_id_name>/users/<user_email>', methods=['PUT', 'PATCH'])
@load_user
def org_add_user(user, org_id_name, user_email):

    if not user.admin:
        raise AuthError(
            'You must be an admin to add a user to an organization.')

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError('You are not allowed to edit this organization.')

    # get this new user by id / email

    # check for int / str
    try:
        user_email = int(user_email)
        user_str = False
    except:
        user_str = True

    if user_str:
        new_org_user = User.query.filter_by(email=user_email).first()
    else:
        new_org_user = User.query.get(user_email)

    if not new_org_user:
        raise RequestError('User "{}" does not exist'
                           .format(user_email))

    # ensure that user is not already a part of this organization.
    if new_org_user.id in org.user_ids:
        raise RequestError('User "{}" is already a part of Organization "{}"'
                           .format(new_org_user.email, org.name))

    org.users.append(new_org_user)
    db.session.commit()

    return jsonify(new_org_user)


@bp.route('/api/v1/orgs/<org_id_name>/users/<user_email>', methods=['DELETE'])
@load_user
def org_remove_user(user, org_id_name, user_email):

    if not user.admin:
        raise AuthError(
            'You must be an admin to remove a user from an organization.')

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this organization.")

    # get this new user by id / email

    # check for int / str
    try:
        user_email = int(user_email)
        user_str = False
    except:
        user_str = True

    if user_str:
        existing_user = User.query.filter_by(email=user_email).first()
    else:
        existing_user = User.query.get(user_email)

    if not existing_user:
        raise RequestError('User "{}" does not yet exist'
                           .format(user_email))

    # ensure that user is not already a part of this organization.
    if existing_user.id not in org.user_ids:
        raise RequestError('User "{}" is not a part of Organization "{}"'
                           .format(existing_user.email, org.name))

    org.users.remove(existing_user)

    if arg_bool('force', False):
        if len(user.org_ids) == 1:
            db.session.delete(user)
    db.session.commit()
    return delete_response()


@bp.route('/api/v1/orgs/<org_id_name>/settings', methods=['GET'])
@load_user
def org_settings(user, org_id_name):

    if not user.admin:
        raise AuthError(
            'You must be an admin to add a user to an organization.')

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    return jsonify(org.settings)


@bp.route('/api/v1/orgs/<org_id_name>/settings', methods=['POST', 'PUT', 'PATCH'])
@load_user
def org_add_setting(user, org_id_name):

    if not user.admin:
        raise ForbiddenError(
            'You must be an admin to add a user to an organization.')

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this organization.")

    # get the request data
    req_data = request_data()

    id = req_data.get('id')
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

    if id:
        s = Setting.query\
            .filter_by(organization_id=org.id, id=id)\
            .first()
    elif name:
        s = Setting.query\
            .filter_by(organization_id=org.id, name=name)\
            .first()
    else:
        raise RequestError(
            "You must pass in a setting 'id' or 'name' to upsert it. "
            "You only passed in: {}".format(", ".join(req_data.keys())))

    if not s:
        if not name or not value:
            raise RequestError(
                "You must pass in a 'name' and 'value' to create a setting. "
                "You only passed in: {}".format(", ".join(req_data.keys())))

        s = Setting(
            organization_id=org.id,
            name=name,
            value=value,
            json_value=json_value or False)

    else:
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


@bp.route('/api/v1/orgs/<org_id_name>/settings/<name>', methods=['GET'])
@load_user
def org_setting(user, org_id_name, name):

    if not user.admin:
        raise ForbiddenError(
            'You must be an admin to add a user to an organization.')

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this organization.")

    s = Setting.query\
        .filter_by(organization_id=org.id, name=name)\
        .first()

    if not s:
        raise RequestError('Setting "{}" does not yet exist for Organization "{}"'
                           .format(name, org.name))

    return jsonify(s)


@bp.route('/api/v1/orgs/<org_id_name>/settings/<name>', methods=['DELETE'])
@load_user
def org_delete_setting(user, org_id_name, name):

    if not user.admin:
        raise AuthError(
            'You must be an admin to add a user to an organization.')

    # check for int / str
    try:
        org_id_name = int(org_id_name)
        org_str = False
    except:
        org_str = True

    if org_str:
        org = Organization.query.filter_by(name=org_id_name).first()
    else:
        org = Organization.query.get(org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This organization does not exist.')

    # ensure the active user can edit this organization
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this organization.")

    # check for int / str
    try:
        name = int(name)
        s_str = False
    except:
        s_str = True

    if s_str:
        s = Setting.query\
            .filter_by(organization_id=org.id, name=name)\
            .first()
    else:
        s = Setting.query\
            .filter_by(organization_id=org.id, id=name)\
            .first()

    if not s:
        raise RequestError('Setting "{}" does not yet exist for Organization "{}"'
                           .format(name, org.name))

    db.session.delete(s)
    db.session.commit()

    return delete_response()
