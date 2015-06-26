from functools import wraps

from newslynx.models.util import fetch_by_id_or_field
from newslynx.views.util import localize
from newslynx.models import User, Org
from newslynx.exc import (
    AuthError, ForbiddenError, NotFoundError)
from newslynx.views.util import arg_str


def load_user(f):
    """
    Check for an apikey and get user object before executing a request.
    """
    @wraps(f)
    def decorated_function(*args, **kw):

        # if we got an apikey...
        apikey = arg_str('apikey', default=None)
        if not apikey:
            raise AuthError(
                'An apikey is required for this request.')

        # get the user object.
        user = User.query\
            .filter_by(apikey=apikey)\
            .first()

        # if it doesn't exist, throw an error
        if not user:
            raise ForbiddenError(
                'Invalid apikey')

        kw['user'] = user
        return f(*args, **kw)

    return decorated_function


def load_org(f):
    """
    Check for an apikey and get user / org object before executing a request.
    """

    @wraps(f)
    def decorated_function(*args, **kw):

        # get the org
        org_id = arg_str('org', default=None)
        if not org_id:
            raise AuthError(
                'An org is required for this request.')

        # get the user object.
        user = kw.get('user')

        org = fetch_by_id_or_field(Org, 'slug', org_id)

        # if it still doesn't exist, raise an error.
        if not org:
            raise NotFoundError(
                'An Org with ID/Slug {} does exist.'
                .format(org_id))

        # otherwise ensure the active user can edit this Org
        if user.id not in org.user_ids:
            raise ForbiddenError(
                'User "{}" is not allowed to access Org "{}".'
                .format(user.name, org.name))

        # check if we should localize this request
        localize(org)

        kw['org'] = org
        return f(*args, **kw)

    return decorated_function
