from time import time
import logging
from traceback import format_exc 

from flask import request
from werkzeug.exceptions import HTTPException

from newslynx.core import app, db
from newslynx.exc import ERRORS
from newslynx.lib.serialize import jsonify
from newslynx.views.util import (
    register_blueprints, error_response)
from newslynx.views import api
from newslynx.views import admin
from newslynx.views import auth
from newslynx import settings


log = logging.getLogger(__name__)

@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(409)
@app.errorhandler(410)
@app.errorhandler(422)
@app.errorhandler(500)
def handle_exceptions(exc):

    if ERRORS.get(exc.__class__.__name__):
        return error_response(exc.__class__.__name__, exc)

    elif isinstance(exc, HTTPException):
        message = exc.get_description(request.environ)
        message = message.replace('<p>', '').replace('</p>', '')
        body = {
            'status_code': exc.code,
            'error': exc.name,
            'message': message
        }
        headers = exc.get_headers(request.environ)

    else:

        body = {
            'status_code': 500,
            'error': exc.__class__.__name__,
            'message': format_exc()
        }
        headers = {}

    return jsonify(body, status=body.get('status_code'),
                   headers=headers)


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
    db.session.remove()


# register blueprints
register_blueprints(app, api, admin, auth)
