from functools import wraps

from flask import request


from flask import after_this_request, request
from cStringIO import StringIO as IO
import gzip
import functools 
from newslynx.models import User, Org
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError)


def load_user(f):
    """
    Check for an apikey and get user object before executing a request.
    """
    @wraps(f)
    def decorated_function(*args, **kw):

        # if we got an apikey...
        apikey = request.args.get('apikey')
        if not apikey:
            raise AuthError('An apikey is required for this request.')

        # get the user object.
        user = User.query.filter_by(apikey=apikey).first()

        # if it doesn't exist, throw an error
        if not user:
            raise ForbiddenError('Invalid apikey')

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
        org_id = request.args.get('org')

        # check for int / str
        try:
            org_id = int(org_id)
            org_str = False
        except:
            org_str = True

        if not org_id:
            raise AuthError('An "org" is required for this request.')

        # get the user object.
        user = kw.get('user')

        if org_str:
            org = Org.query.filter_by(name=org_id).first()
        else:
            org = Org.query.get(org_id)

        # if it still doesn't exist, raise an error.
        if not org:
            raise RequestError('An Org with ID/Name {} does exist.'
                               .format(org_id))

        # otherwise ensure the active user can edit this Org
        if user.id not in org.user_ids:
            raise ForbiddenError('User "{}" is not allowed to access Org "{}".'
                                 .format(user.name, org.name))

        kw['org'] = org
        return f(*args, **kw)

    return decorated_function


def cache_key(*args, **kw):
    """
    Create a caching key for redis from a request object.
    """

    path = request.path
    args = str(hash(frozenset(request.args.items()))).encode('utf-8')
    return 'newslynx-cache:{}:{}'.format(path, args)

def gzipped(f):
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                response.status_code >= 300 or
                'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb', 
                                      fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func