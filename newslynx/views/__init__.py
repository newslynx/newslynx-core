from time import time
import logging

from flask import request
from werkzeug.exceptions import HTTPException

from newslynx.core import app
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError, NotFoundError)
from newslynx.lib.serialize import jsonify
from newslynx.views.util import register_blueprints
from newslynx.views import api
from newslynx.views import admin
from newslynx.views import oauth

log = logging.getLogger(__name__)


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
            'name': exc.name,
            'message': message
        }
        headers = exc.get_headers(request.environ)

    else:
        body = {
            'status': 500,
            'name': exc.__class__.__name__,
            'message': unicode(exc)
        }
        headers = {}

    return jsonify(body, status=body.get('status'),
                   headers=headers)


@app.errorhandler(AuthError)
def handle_auth_error(error):
    response = jsonify(error)
    response.status_code = error.status_code
    return response


@app.errorhandler(RequestError)
def handle_request_error(error):
    response = jsonify(error)
    response.status_code = error.status_code
    return response


@app.errorhandler(ForbiddenError)
def handle_forbidden_error(error):
    response = jsonify(error)
    response.status_code = error.status_code
    return response


@app.errorhandler(NotFoundError)
def handle_not_found_error(error):
    response = jsonify(error)
    response.status_code = error.status_code
    return response


@app.before_request
def begin_timing():
    request._begin_time = time()


@app.after_request
def end_timing(response):
    if app.config.get('DEBUG_TIMING'):
        duration = (time() - request._begin_time) * 1000
        log.info('Request to \'%s\' (args: %r) took: %dms',
                 request.path, request.args.items(), duration)
    return response

# register blueprints
register_blueprints(app, api, admin, oauth)
