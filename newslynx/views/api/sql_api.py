"""
The super user can submit sql queries to the API.
"""
from flask import Blueprint, Response, stream_with_context, request

from sqlalchemy.exc import ResourceClosedError
from newslynx.core import db
from newslynx.exc import RequestError, ForbiddenError
from newslynx.views.decorators import load_user
from newslynx.lib.serialize import obj_to_json
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data
from newslynx.tasks.util import ResultIter
from newslynx.views.util import arg_str, arg_bool


# bp
bp = Blueprint('sql', __name__)


@bp.route('/api/v1/sql', methods=['POST', 'GET'])
@load_user
def exec_query(user):
    """
    Only the super user can access the sql api.
    This is primarily intended for internal recipes
    which may operate on machines without access to
    the databse.
    """
    if not user.super_user:
        raise ForbiddenError(
            "Only the super user can access the SQL API.")
    if request.method == "POST":
        q = request_data().get('query', None)
    if request.method == "GET":
        q = arg_str('query', default=None)
    if not q:
        raise RequestError('A query - "q" is required.')
    stream = arg_bool('stream', default=True)
    try:
        results = db.session.execute(q)
    except Exception as e:
        raise RequestError(
            "There was an error executing this query: "
            "{}".format(e.message))

    def generate():
        try:
            for row in ResultIter(results):
                if stream:
                    yield obj_to_json(row) + "\n"
                else:
                    yield row
        except ResourceClosedError:
            resp = {'success': True}
            if stream:
                yield obj_to_json(resp) + "\n"
            else:
                yield resp
    if stream:
        return Response(stream_with_context(generate()))

    data = list(generate())
    if len(data) == 1:
        if data[0]['success']:
            data = data[0]
    return jsonify(data)
