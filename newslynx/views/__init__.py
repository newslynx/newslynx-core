from time import time
import logging

from flask import request
from werkzeug.exceptions import HTTPException

from newslynx.core import app, db, db_session
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError, NotFoundError,
    SousChefSchemaError, ConfigError, SearchStringError,
    UnprocessableEntityError)
from newslynx.lib.serialize import jsonify
from newslynx.views.util import (
    register_blueprints, error_response)
from newslynx.views import api
from newslynx.views import admin
from newslynx.views import auth
from newslynx import settings

log = logging.getLogger(__name__)

# register blueprints
register_blueprints(app, api, admin, auth)


@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(410)
@app.errorhandler(500)
def handle_exceptions(exc):

    if isinstance(exc, HTTPException):
        message = exc.get_description(request.environ)
        message = message.replace('<p>', '').replace('</p>', '')
        body = {
            'status': exc.code,
            'error': exc.name,
            'message': message
        }
        headers = exc.get_headers(request.environ)

    else:
        body = {
            'status': 500,
            'error': exc.__class__.__name__,
            'message': unicode(exc)
        }
        headers = {}

    return jsonify(body, status=body.get('status'),
                   headers=headers)


@app.errorhandler(AuthError)
def handle_auth_error(error):
    return error_response('AuthError', error)


@app.errorhandler(RequestError)
def handle_request_error(error):
    return error_response('RequestError', error)


@app.errorhandler(ForbiddenError)
def handle_forbidden_error(error):
    return error_response('ForbiddenError', error)


@app.errorhandler(NotFoundError)
def handle_not_found_error(error):
    return error_response('NotFoundError', error)


@app.errorhandler(UnprocessableEntityError)
def handle_unprocessable_entity_error(error):
    return error_response('UnprocessableEntityError', error)


@app.errorhandler(SousChefSchemaError)
def handle_sous_chef_schema_error(error):
    return error_response('SousChefSchemaError', error)


@app.errorhandler(ConfigError)
def handle_config_error(error):
    return error_response('ConfigError', error)


@app.errorhandler(SearchStringError)
def handle_search_string_error(error):
    return error_response('SearchStringError', error)


@app.before_request
def begin_timing():
    request._begin_time = time()


@app.after_request
def end_timing(response):
    if getattr(settings, 'LOG_TIMING', False):
        duration = (time() - request._begin_time) * 1000
        log.info('Request to \'%s\' (args: %r) took: %dms',
                 request.path, request.args.items(), duration)
    return response


@app.teardown_appcontext
def shutdown_sessions(exception=None):
    db_session.remove()
