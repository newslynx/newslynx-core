import logging

from flask import Blueprint

from newslynx.core import db
from newslynx.models import User, Org
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib import mail
from newslynx.tasks import default
from newslynx.lib.serialize import jsonify
from newslynx.lib.text import slug
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError, NotFoundError,
    ConflictError)
from newslynx.views.decorators import load_user
from newslynx.views.util import (
    request_data, delete_response, arg_bool, localize)
# bp
bp = Blueprint('orgs', __name__)

log = logging.getLogger(__name__)


@bp.route('/api/v1/orgs', methods=['GET'])
@load_user
def me_orgs(user):
    return jsonify(user.orgs)


@bp.route('/api/v1/orgs', methods=['POST'])
@load_user
def org_create(user):

    req_data = request_data()

    if not user.super_user:
        raise ForbiddenError(
            'You must be the super user to create an Org')

    if 'name' not in req_data \
       or 'timezone' not in req_data:
        raise RequestError(
            "An Org requires a 'name' and 'timezone")

    org = default.org(
        name=req_data['name'],
        timezone=req_data['timezone']
    )
    db.session.commit()
    return jsonify(org)


@bp.route('/api/v1/orgs/<int:org_id>', methods=['GET'])
@load_user
def org(user, org_id):

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'Org {} does not exist.'.format(org_id))

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    # localize
    localize(org)

    return jsonify(org.to_dict(incl_domains=True))


@bp.route('/api/v1/orgs/<int:org_id>/simple-content', methods=['GET'])
@load_user
def org_content(user, org_id):
    """
    Return a simple list of all content items an organization owns.
    """
    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'Org {} does not exist.'.format(org_id))

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    # localize
    localize(org)

    return jsonify(org.simple_content_items)


@bp.route('/api/v1/orgs/<int:org_id>', methods=['PUT', 'PATCH'])
@load_user
def org_update(user, org_id):

    req_data = request_data()

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    # if the org doesnt exist, create it.
    if not org:
        raise NotFoundError(
            'Org {} does not exist.'.format(org_id))

    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this Org.")

    # localize
    localize(org)

    # update the requesting user to the org
    if 'name' in req_data:
        org.name = req_data['name']

    if 'slug' in req_data:
        org.slug = req_data['slug']

    elif 'name' in req_data:
        org.slug = slug(req_data['name'])

    if 'timezone' in req_data:
        org.timezone = req_data['timezone']

    try:
        db.session.add(org)
        db.session.commit()

    except Exception as e:
        raise RequestError(
            "An error occurred while updating this Org '{}'. "
            "Here's the error message: {}"
            .format(org.name, e.message))

    return jsonify(org)


@bp.route('/api/v1/orgs/<int:org_id>', methods=['DELETE'])
@load_user
def org_delete(user, org_id):

    if not user.admin:
        raise AuthError(
            'You must be an admin to delete an Org')

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'Org {} does not exist.'.format(org_id))

    # localize
    localize(org)

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'User "{}" is not allowed to access Org "{}".'
            .format(user.name, org.name))

    db.session.delete(org)
    db.session.commit()

    return delete_response()


@bp.route('/api/v1/orgs/<int:org_id>/users',  methods=['GET'])
@load_user
def org_users(user, org_id):

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError(
            'Org {} does not exist.'.format(org_id))

    # localize
    localize(org)

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'User "{}" is not allowed to access Org "{}".'
            .format(user.email, org.name))

    return jsonify(org.users)


@bp.route('/api/v1/orgs/<int:org_id>/users',  methods=['POST'])
@load_user
def org_create_user(user, org_id):

    if not user.admin:
        raise AuthError(
            'You must be an admin to create a user for an Org.')

    # get the form.
    req_data = request_data()
    email = req_data.get('email')
    password = req_data.get('password')
    name = req_data.get('name')
    admin = req_data.get('admin', False)

    if not all([email, password, name]):
        raise RequestError(
            'An email, password, and name are required to create a User.')

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError('This Org does not exist.')

    # localize
    localize(org)

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this Org.")

    if User.query.filter_by(email=email).first():
        raise ConflictError(
            'A User with email "{}" already exists'
            .format(email))

    if not mail.validate(email):
        raise RequestError(
            '{} is an invalid email address.'
            .format(email))

    new_org_user = User(
        email=email,
        password=password,
        name=name,
        admin=admin)

    org.users.append(new_org_user)
    db.session.commit()

    return jsonify(new_org_user)


@bp.route('/api/v1/orgs/<int:org_id>/users/<user_email>',  methods=['GET'])
@load_user
def org_user(user, org_id, user_email):

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    if not org:
        raise NotFoundError(
            'Org {} does not exist.'.format(org_id))

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to access this Org')

    # localize
    localize(org)

    # get this new user by id / email
    org_user = fetch_by_id_or_field(User, 'email', user_email)

    if not org_user:
        raise RequestError(
            'This user does not yet exist')

    # check whether this user can view this other user:
    if not len(list(set(org_user.org_ids).intersection(set(user.org_ids)))):
        raise ForbiddenError(
            'You are not allowed to view this user.'
            .format(user.email))

    return jsonify(org_user)


@bp.route('/api/v1/orgs/<int:org_id>/users/<user_email>', methods=['PUT', 'PATCH'])
@load_user
def org_add_user(user, org_id, user_email):

    if not user.admin:
        raise AuthError(
            'You must be an admin to add a user to an Org.')

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    if not org:
        raise NotFoundError(
            'Org {} does not exist.'.format(org_id))

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            'You are not allowed to edit this Org.')

    # localize
    localize(org)

    # get this new user by id / email
    new_org_user = fetch_by_id_or_field(User, 'email', user_email)

    # get the form.
    req_data = request_data()
    email = req_data.get('email')
    name = req_data.get('name')
    admin = req_data.get('admin', False)
    password = req_data.get('password')

    if email and not mail.validate(email):
        raise RequestError(
            '{} is an invalid email address.'
            .format(email))

    # insert
    if not new_org_user:
        if not all([email, password, name]):
            raise RequestError(
                'An email, password, and name are required to create a User.')

        new_org_user = User(
            email=email,
            password=password,
            name=name,
            admin=admin)
        org.users.append(new_org_user)
        db.session.add(org)

    # ensure the active user can edit this Org
    elif new_org_user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this Org.")

    # update
    if name:
        new_org_user.name = name
    if email:
        new_org_user.email = email
    if admin:
        new_org_user.admin = admin
    if password:
        new_org_user.set_password(password)

    new_org_user.admin = admin
    db.session.add(new_org_user)
    db.session.commit()
    return jsonify(new_org_user)


@bp.route('/api/v1/orgs/<int:org_id>/users/<user_email>', methods=['DELETE'])
@load_user
def org_remove_user(user, org_id, user_email):

    if not user.admin:
        raise AuthError(
            'You must be an admin to remove a user from an Org.')

    # fetch org
    org = fetch_by_id_or_field(Org, 'slug', org_id)

    # if it still doesn't exist, raise an error.
    if not org:
        raise NotFoundError('This Org does not exist.')

    # localize
    localize(org)

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this Org.")

    # get this existing user by id / email
    existing_user = fetch_by_id_or_field(User, 'email', user_email)

    if not existing_user:
        raise RequestError(
            'User "{}" does not yet exist'
            .format(user_email))

    # ensure that user is not already a part of this Org.
    if existing_user.id not in org.user_ids:
        raise RequestError(
            'User "{}" is not a part of Org "{}"'
            .format(existing_user.email, org.name))

    # remove the user from the org
    org.users.remove(existing_user)

    # if we're force-deleting the user, do so
    # but make sure their recipes are re-assigned
    # to the super-user
    if arg_bool('force', False):
        cmd = "UPDATE recipes set user_id={} WHERE user_id={}"\
              .format(org.super_user.id, existing_user.id)
        db.session.execute(cmd)
        db.session.delete(user)

    db.session.commit()
    return delete_response()
