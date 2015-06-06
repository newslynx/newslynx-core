from flask import Blueprint

from newslynx.core import db
from newslynx.lib.serialize import jsonify
from newslynx.exc import (
    AuthError, RequestError, ForbiddenError, NotFoundError)
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import *

# bp
bp = Blueprint('sql', __name__)


@bp.route('/api/v1/sql', methods=['GET'])
@load_user
def exec_query(user):
    q = arg_str('q', default=None)
    if not q:
        raise RequestError('A query string - "q" - is required')


