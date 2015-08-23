from flask import Blueprint

from newslynx.core import db
from newslynx.models import User
from newslynx.lib.serialize import jsonify
from newslynx.lib import mail
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError)
from newslynx.views.decorators import load_user
from newslynx.core import settings
from newslynx.views.util import (
    request_data, delete_response, arg_bool)

# bp
bp = Blueprint('users', __name__)


@bp.route('/api/v1/login', methods=['POST'])
def login():
    """
    Login a user and return his/her apikey.
    """

    # parse post body
    req_data = request_data()
    email = req_data.get('email')
    password = req_data.get('password')

    # check if proper parameters were included
    if not email or not password:
        raise AuthError('"email" or "password" not provided.')

    # check user's existence
    user = User.query\
        .filter_by(email=email)\
        .first()

    if user is None:
        raise AuthError('A user with email "{}" does not exist.'
                        .format(email))

    # check the supplied password if not the super user
    if password != settings.SUPER_USER_PASSWORD:
        if not user.check_password(password):
            raise ForbiddenError('Invalid password.')

    return jsonify(user.to_dict(incl_apikey=True))


@bp.route('/auth/v1/login', methods=['POST'])
def app_login():
    """
    A special endpoint for the app.
    """
    return login()


@bp.route('/api/v1/me', methods=['GET'])
@load_user
def me(user):
    """
    Get yourself.
    """
    return jsonify(user.to_dict(incl_apikey=True))


@bp.route('/api/v1/me', methods=['PUT', 'PATCH'])
@load_user
def update_me(user):
    """
    Update yourself.
    """

    # get the form.
    req_data = request_data()

    email = req_data.get('email')
    old_password = req_data.get('old_password')
    new_password = req_data.get('new_password')
    name = req_data.get('name')

    # edit user.
    if email:
        # validate the email address:
        if not mail.validate(email):
            raise RequestError(
                "'{}' is not a valid email address."
                .format(email))
        user.email = email

    if old_password and new_password:
        if not user.check_password(old_password):
            raise ForbiddenError('Invalid password.')
        user.set_password(new_password)

    if name:
        user.name = name

    # check if we should refresh the apikey
    if arg_bool('refresh_apikey', False):
        user.set_apikey()

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict(incl_apikey=True))


@bp.route('/api/v1/me', methods=['DELETE'])
@load_user
def delete_me(user):
    """
    Permanently delete yourself.
    Assigns all of the recipes you've
    created to the super user.
    """

    # get the super user
    super_user = User.query\
        .filter_by(email=settings.SUPER_USER_EMAIL)\
        .first()

    # reassign this user's recipes to the super user
    cmd = "UPDATE recipes set user_id={} WHERE user_id={};"\
          .format(super_user.id, user.id)
    db.session.execute(cmd)

    # delete this user
    db.session.delete(user)
    db.session.commit()

    # return
    return delete_response()
