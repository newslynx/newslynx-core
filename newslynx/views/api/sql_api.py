from flask import Blueprint, Response, stream_with_context
from sqlalchemy.exc import ResourceClosedError
from newslynx.core import db
from newslynx.exc import RequestError, ForbiddenError
from newslynx.views.decorators import load_user
from newslynx.lib.serialize import obj_to_json
from newslynx.views.util import request_data
from newslynx.models.util import ResultIter


# bp
bp = Blueprint('sql', __name__)


@bp.route('/api/v1/sql', methods=['POST'])
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

    q = request_data().get('query', None)
    if not q:
        raise RequestError('A query - "q" is required.')

    try:
        results = db.session.execute(q)
    except Exception as e:
        raise RequestError(
            "There was an error executing this query: "
            "{}".format(e.message))

    def generate():
        try:
            for row in ResultIter(results):
                yield obj_to_json(row) + "\n"
        except ResourceClosedError:
            yield obj_to_json({'success': True}) + "\n"

    return Response(stream_with_context(generate()))
