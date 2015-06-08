from flask import Blueprint

from newslynx.lib.serialize import jsonify
from newslynx.lib import dates
from newslynx.lib import shares
from newslynx.models import ExtractCache
from newslynx.views.util import arg_str, arg_bool
from newslynx.views.decorators import load_user
from newslynx.exc import RequestError, InternalServerError

# bp
bp = Blueprint('urls', __name__)

# a cache to optimize calls to this api
extract_cache = ExtractCache()


@bp.route('/api/v1/urls/extract', methods=['GET'])
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
    if not cr:
        extract_cache.invalidate(url, type)
        raise InternalServerError('Something went wrong. Try again.')

    resp = {
        'cache': cr,
        'data': cr.value
    }
    return jsonify(resp)


@bp.route('/api/v1/urls/share-counts', methods=['GET'])
@load_user
def share_counts(user):
    url = arg_str('url', default=None)
    data = shares.count(url)
    data['datetime'] = dates.floor_now()
    return jsonify(data)
