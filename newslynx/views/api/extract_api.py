from flask import Blueprint, render_template

from newslynx.lib.serialize import jsonify
from newslynx.models import ExtractCache
from newslynx.views.util import arg_str, arg_bool
from newslynx.views.decorators import load_user
from newslynx.exc import RequestError, InternalServerError
from newslynx.util import here

# bp
tmpl_folder = here(__file__, 'templates/')
bp = Blueprint('extract', __name__, template_folder=tmpl_folder)

# a cache to optimize calls to this api
extract_cache = ExtractCache()


@bp.route('/api/v1/extract', methods=['GET'])
@load_user
def extract(user):
    url = arg_str('url', default=None)
    type = arg_str('type', default='article')
    force_refresh = arg_bool('force_refresh', default=False)
    format = arg_str('format', default='json')

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

    if format == 'html':
        return render_template(
            'extract_preview.html',
            data=resp)

    return jsonify(resp)
