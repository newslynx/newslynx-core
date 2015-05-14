from flask import Blueprint, request

from newslynx.core import db
from newslynx.models import User, Org, SousChef, Recipe, Tag
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError)
from newslynx.views.decorators import load_user
from newslynx.views.util import (
    request_data, BOOL_TRUISH, delete_response, arg_bool)
from newslynx.init import load_default_tags, load_default_recipes
from newslynx.exc import RecipeSchemaError

# bp
bp = Blueprint('orgs', __name__)


@bp.route('/api/v1/orgs', methods=['GET'])
@load_user
def me_orgs(user):
    return jsonify(user.orgs)


@bp.route('/api/v1/orgs', methods=['POST'])
@load_user
def org_create(user):

    req_data = request_data()

    if not user.admin:
        raise ForbiddenError(
            'You must be an admin to create or update an Org')

    org = Org.query.filter_by(name=req_data['name']).first()

    # if the org doesnt exist, create it.
    if org:
        raise RequestError(
            "Org '{}' already exists".format(req_data['name']))

    # add the requesting user to the org
    org = Org(name=request.form['name'])
    org.users.append(user)
    db.session.add(org)

    # add default tags
    for tag in load_default_tags():
        tag['org_id'] = org.id
        t = Tag(**tag)
        db.session.add(t)

    # add default recipes
    for recipe in load_default_recipes():
        recipe['user_id'] = user.id
        recipe['status'] = 'uninitialized'
        sous_chef_slug = recipe.pop('sous_chef')
        if not sous_chef_slug:
            raise RecipeSchemaError(
                'Default recipe "{}" is missing a "sous_chef" slug.'
                .format(recipe.get('name', '')))

        sc = SousChef.query.filter_by(slug=sous_chef_slug).first()
        if not sc:
            raise RecipeSchemaError(
                '"{}" is not a valid SousChef slug or the SousChef does not yet exist.'
                .format(recipe['name']))
        r = Recipe(sc, **recipe)
        db.session.add(r)

    db.session.commit()

    return jsonify(org)


@bp.route('/api/v1/orgs/<org_id_name>', methods=['GET'])
@load_user
def org(user, org_id_name):

    # fetch org
    org = fetch_by_id_or_field(Org, 'name', org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError('You are not allowed to access this Org')

    return jsonify(org)


@bp.route('/api/v1/orgs/<org_id_name>', methods=['PUT', 'PATCH'])
@load_user
def org_update(user, org_id_name):

    req_data = request_data()

    if not user.admin:
        raise ForbiddenError(
            'You must be an admin to create or update an Org')

    # fetch org
    org = fetch_by_id_or_field(Org, 'name', org_id_name)

    # if the org doesnt exist, create it.
    if not org:
        raise RequestError(
            "Org '{}' Does not exists".format(req_data['name']))

    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this Org.")

    # update the requesting user to the org
    if 'name' in req_data:
        org.name = req_data['name']
    if 'slug' in req_data:
        org.slug = req_data['slug']
    db.session.add(org)
    db.session.commit()

    return jsonify(org)


@bp.route('/api/v1/orgs/<org_id_name>', methods=['DELETE'])
@load_user
def org_delete(user, org_id_name):

    if not user.admin:
        raise AuthError('You must be an admin to delete an Org')

    # fetch org
    org = fetch_by_id_or_field(Org, 'name', org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError('User "{}" is not allowed to access Org "{}".'
                             .format(user.name, org.name))

    db.session.delete(org)
    db.session.commit()

    return delete_response()


@bp.route('/api/v1/orgs/<org_id_name>/users',  methods=['GET'])
@load_user
def org_users(user, org_id_name):

    # fetch org
    org = fetch_by_id_or_field(Org, 'name', org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError('User "{}" is not allowed to access Org "{}".'
                             .format(user.email, org.name))

    return jsonify(org.users)


@bp.route('/api/v1/orgs/<org_id_name>/users',  methods=['POST'])
@load_user
def org_create_user(user, org_id_name):

    if not user.admin:
        raise AuthError(
            'You must be an admin to create a user for an Org.')

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

    # fetch org
    org = fetch_by_id_or_field(Org, 'name', org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this Org.")

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

    # fetch org
    org = fetch_by_id_or_field(Org, 'name', org_id_name)

    if not org:
        raise RequestError('This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError('You are not allowed to access this Org')

    # get this new user by id / email
    org_user = fetch_by_id_or_field(User, 'email', user_email)

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
            'You must be an admin to add a user to an Org.')

    # fetch org
    org = fetch_by_id_or_field(Org, 'name', org_id_name)

    if not org:
        raise RequestError('This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError('You are not allowed to edit this Org.')

    # get this new user by id / email
    new_org_user = fetch_by_id_or_field(User, 'email', user_email)

    if not new_org_user:
        raise RequestError('User "{}" does not exist'
                           .format(user_email))

    # ensure that user is not already a part of this Org.
    if new_org_user.id in org.user_ids:
        raise RequestError('User "{}" is already a part of Org "{}"'
                           .format(new_org_user.email, org.name))

    org.users.append(new_org_user)
    db.session.commit()

    return jsonify(new_org_user)


@bp.route('/api/v1/orgs/<org_id_name>/users/<user_email>', methods=['DELETE'])
@load_user
def org_remove_user(user, org_id_name, user_email):

    if not user.admin:
        raise AuthError(
            'You must be an admin to remove a user from an Org.')

    # fetch org
    org = fetch_by_id_or_field(Org, 'name', org_id_name)

    # if it still doesn't exist, raise an error.
    if not org:
        raise RequestError('This Org does not exist.')

    # ensure the active user can edit this Org
    if user.id not in org.user_ids:
        raise ForbiddenError(
            "You are not allowed to access this Org.")

    # get this existing user by id / email
    existing_user = fetch_by_id_or_field(User, 'email', user_email)

    if not existing_user:
        raise RequestError('User "{}" does not yet exist'
                           .format(user_email))

    # ensure that user is not already a part of this Org.
    if existing_user.id not in org.user_ids:
        raise RequestError('User "{}" is not a part of Org "{}"'
                           .format(existing_user.email, org.name))

    org.users.remove(existing_user)

    if arg_bool('force', False):
        if len(user.org_ids) == 1:
            db.session.delete(user)
    db.session.commit()

    return delete_response()
