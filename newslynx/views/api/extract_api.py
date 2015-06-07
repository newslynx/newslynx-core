from flask import Blueprint

from newslynx.lib.serialize import jsonify
from newslynx.models import ExtractCache
from newslynx.views.util import arg_str, arg_bool
from newslynx.views.decorators import load_user
from newslynx.exc import RequestError

# bp
bp = Blueprint('extract', __name__)

# a cache to optimize calls to this api
extract_cache = ExtractCache()


@bp.route('/api/v1/extract', methods=['GET'])
@load_user
def extract(user):
    url = arg_str('url', default=None)
    type = arg_str('type', default='article')
    force_refresh = arg_bool('force_refresh', default=False)

    if not url:
        raise RequestError("A url is required.")

    if force_refresh:
        extract_cache.debug = True

    cr = extract_cache.get(url, type)
    resp = {
        'cache': cr,
        'data': cr.value
    }
    return jsonify(resp)
