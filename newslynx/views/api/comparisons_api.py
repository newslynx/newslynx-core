import logging

from flask import Blueprint

from newslynx.views.decorators import load_user, load_org
from newslynx.exc import NotFoundError, RequestError, InternalServerError
from newslynx.lib.serialize import jsonify
from newslynx.constants import CONTENT_METRIC_COMPARISONS
from newslynx.models import (
    ComparisonsCache, AllContentComparisonCache,
    SubjectTagsComparisonCache,
    ContentTypeComparisonCache,
    ImpactTagsComparisonCache)

from newslynx.views.util import arg_bool

# blueprint
bp = Blueprint('comparisons', __name__)

log = logging.getLogger(__name__)

comparisons_cache = ComparisonsCache()
comparison_types = {
    'content': {
        'all': AllContentComparisonCache(),
        'impact_tags': ImpactTagsComparisonCache(),
        'subject_tags': SubjectTagsComparisonCache(),
        'types': ContentTypeComparisonCache()
    },
    'orgs': {

    }
}


# helpers for comparisons

def parse_comparison_type(type, level):
    """
    Parse a comparison type.
    """
    if type not in comparison_types[level].keys():
        raise RequestError(
            "'{}' is an invalid {} comparison. Choose from {}"
            .format(type, level, ", ".join(CONTENT_METRIC_COMPARISONS)))
    return type


def parse_comparison_level(level):
    """
    Validate comparison levels.
    """
    if level not in ['content', 'orgs']:
        raise NotFoundError('URL Not Found')
    return level


def get_comparison(*args, **kwargs):
    """
    Get a single comparison.
    """
    level = kwargs.pop('level')
    type = kwargs.pop('type')
    level = parse_comparison_level(level)
    type = parse_comparison_type(type, level)
    refresh = arg_bool('refresh', default=False)
    cache_details = arg_bool('cache_details', default=False)
    fx = comparison_types[level][type]
    if refresh:
        fx.invalidate(*args, **kwargs)
    cr = fx.get(*args, **kwargs)
    if refresh and cr.is_cached:
        raise InternalServerError(
            'Something went wrong with the cache invalidation process.')
    if cache_details:
        return jsonify({'cache': cr, 'comparisons': cr.value})
    return jsonify(cr.value)


def refresh_comparison(org, level, type):
    """
    Refresh a single comparison.
    """
    type = parse_comparison_type(type)
    level = parse_comparison_level(level)
    fx = comparison_types[level][type]
    fx.invalidate(org.id)
    cr = fx.get(org.id)
    if not cr.value or cr.is_cached:
        raise InternalServerError(
            'Something went wrong with the cache invalidation process.')
    return jsonify({'success': True})


@bp.route('/api/v1/<level>/comparisons', methods=['GET'])
@load_user
@load_org
def get_all_comparisons(user, org, level):
    """
    Get all comparisons by level.
    """
    return get_comparison(org, level=level, type='all')


@bp.route('/api/v1/<level>/comparisons', methods=['PUT'])
@load_user
@load_org
def refresh_comparisons(user, org):
    """
    Refresh content comparisons
    """
    return refresh_comparison(org, level=level, type='all')


@bp.route('/api/v1/<level>/comparisons/<type>', methods=['GET'])
@load_user
@load_org
def get_one_content_comparisons(user, org, type):
    """
    Get one content comparison.
    """
    return get_comparison(org, level=level, type=type)

@bp.route('/api/v1/content/comparisons/<type>', methods=['PUT'])
@load_user
@load_org
def refresh_one_content_comparisons(user, org, type):
    """
    Refresh one content comparison.
    """
    return refresh_comparison(org, level=level, type=type)
