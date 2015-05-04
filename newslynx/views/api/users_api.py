from flask import Blueprint

from newslynx.core import db
from newslynx.models import User
from newslynx.lib.serialize import jsonify
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError)
from newslynx.views.decorators import load_user
from newslynx.views.util import request_data, delete_response

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
    user = User.query.filter_by(email=email).first()
    if user is None:
        raise RequestError('A user with email "{}" does not exist.'
                           .format(email))

    # check the supplied password
    if not user.check_password(password):
        raise ForbiddenError('Invalid password.')

    return jsonify(user.to_dict(incl_apikey=True))


@bp.route('/auth/v1/login', methods=['POST'])
def michaels_login():
    """
    A special endpoint for michael's app.
    """
    return login()


@bp.route('/api/v1/me', methods=['GET'])
@load_user
def me(user):
    """
    Get yourself.
    """
    return jsonify(user.to_dict(incl_apikey=True))


@bp.route('/api/v1/me', methods=['PUT', 'POST', 'PATCH'])
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
        user.email = email

    if old_password and new_password:
        if not user.check_password(old_password):
            raise ForbiddenError('Invalid password.')
        user.set_password(new_password)

    if name:
        user.name = name

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict(incl_apikey=True))


@bp.route('/api/v1/me', methods=['DELETE'])
@load_user
def delete_me(user):
    """
    Delete yourself.
    """
    db.session.delete(user)
    db.session.commit()
    return delete_response()
