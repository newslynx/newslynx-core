import logging
from collections import defaultdict

from operator import itemgetter
from flask import Blueprint

from newslynx.views.decorators import load_user, load_org
from newslynx.exc import NotFoundError, RequestError, InternalServerError
from newslynx.lib.serialize import jsonify
from newslynx.constants import CONTENT_METRIC_COMPARISONS
from newslynx.models import (
    ComparisonsCache, AllContentComparisonCache,
    SubjectTagsComparisonCache,
    ContentTypeComparisonCache,
    ImpactTagsComparisonCache,
    OrgMetricSummary, ContentMetricSummary)

from newslynx.views.util import arg_bool

# blueprint
bp = Blueprint('comparisons', __name__)

log = logging.getLogger(__name__)

comparison_types = {
    'content': {
        'all': ComparisonsCache(),
        'impact_tags': ImpactTagsComparisonCache(),
        'subject_tags': SubjectTagsComparisonCache(),
        'types': ContentTypeComparisonCache()
    },
    'orgs': {

    }
}


def response_from_cache(cr):
    """
    Format a response from a cache object.
    """
    if arg_bool('cache_details', default=False):
        resp = jsonify({'cache': cr, 'comparisons': cr.value})
    else:
        resp = jsonify(cr.value)
    resp.headers['Last-Modified'] = cr.last_modified
    return resp


def parse_comparison_type(type, level):
    """
    Parse a comparison type.
    """
    type = type.replace('-', "_")
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
    fx = comparison_types[level][type]
    if refresh:
        fx.invalidate(*args, **kwargs)
    cr = fx.get(*args, **kwargs)
    if refresh and cr.is_cached:
        raise InternalServerError(
            'Something went wrong with the cache invalidation process.')
    return cr


def refresh_comparison(*args, **kwargs):
    """
    Refresh a single comparison.
    """

    # parse kwargs
    level = kwargs.pop('level')
    type = kwargs.pop('type')
    level = parse_comparison_level(level)
    type = parse_comparison_type(type, level)

    fx = comparison_types[level][type]
    fx.invalidate(*args, **kwargs)
    cr = fx.get(*args, **kwargs)
    if not cr.value or cr.is_cached:
        raise InternalServerError(
            'Something went wrong with the cache invalidation process.')
    return cr


def get_comparison_items(level, level_id, org_id):
    """
    Get a comparison item for any level. We can add more functions to
    this as our needs grow.
    """
    fx = {
        'content': ContentMetricSummary.query
                        .filter_by(org_id=org_id)\
                        .filter(ContentMetricSummary.content_item_id.in_(level_id)),
        'orgs': OrgMetricSummary.query
                    .filter(OrgMetricSummary.org_id.in_(level_id)),
    }

    if not isinstance(level_id, list):
        level_id = [level_id]

    if len(level_id) == 1:
        o = fx[level].first()
    else:
        o = fx[level].all()
        if not len(o):
            o = None
    if not o:
        raise NotFoundError(
            "No {} could be found with ids:\n{}"
            .format(level, ",".join(level_id))
        )
    if len(level_id) == 1:
        yield o.to_dict()
    else:
        for oo in o:
            yield oo.to_dict()


def get_item_comparison(*args, **kwargs):
    """
    Create a comparison objects for one or more items.
    """
    key = kwargs.pop('key')
    org_id = kwargs.pop('org_id')
    level_id = kwargs.pop('level_id')
    level = kwargs.get('level')
    items = get_comparison_items(level, level_id, org_id)
    comparisons = get_comparison(*args, **kwargs)
    return compare_many(items, comparisons.value, key)


# Functions for creating percentile comparisons for content items.


def compare_many(items, comparisons, key='metrics'):
    """
    Add a comparisons object to
    """
    for item in items:
        m = item.pop(key)
        item['comparisons'] = compare(m, comparisons)
        yield item


def compare(metrics, comparisons):
    """
    Return percentile rankings given a a dictionary
    of metrics and comparisons.
    """
    output = defaultdict(lambda: defaultdict(dict))
    for metric, comparison in gen_comparisons_lookup(comparisons):
        value = metrics.get(metric, None)
        if comparison['min'] == 0 and comparison['max'] == 0:
            percentile = None
        else:
            percentile = compare_one(value, comparison)
        d = {metric: percentile}
        if not comparison['facet_value']:
            output[comparison['facet']].update(d)
        else:
            output[comparison['facet']][comparison['facet_value']].update(d)
    return output


def gen_comparisons_lookup(comparisons):
    """
    Generate a lookup metrics => comparison facets.
    """
    for facet, values in comparisons.items():
        if isinstance(values, list):
            for value in values:
                value['facet'] = facet
                value['facet_value'] = None
                yield value['metric'], value
        elif isinstance(values, dict):
            for facet_value, vvalues in values.items():
                for value in vvalues:
                    value['facet'] = facet
                    value['facet_value'] = facet_value
                    yield value['metric'], value


def compare_one(value, comparison):
    """
    Given a value and comparison object, return comparison stats.
    """
    # lookup all percentiles.
    percentiles = {
        ('per_50' if k == 'median' else k): float(v)
        for k, v in comparison.items()
        if k.startswith('per_') or k.startswith('median')
    }
    percentiles = dict(sorted(percentiles.items(), key=itemgetter(1)))
    idx, per_value = find_nearest(percentiles.values(), value)
    per = float(percentiles.keys()[idx].replace('per_', '').replace('_5', '.5'))
    return per


def find_nearest(array, value):
    """
    Find the nearest value in an array.
    """
    return min(enumerate(array), key=lambda x: abs(x[1]-value))


@bp.route('/api/v1/<level>/<level_id>/comparisons', methods=['GET'])
@load_user
@load_org
def make_item_comparisons(user, org, level, level_id):
    """
    Get all comparisons by level.
    """
    resp = get_item_comparison(org.id, org_id=org.id, level=level,
                               level_id=level_id, type='all', key='metrics')
    return jsonify(list(resp))


@bp.route('/api/v1/<level>/<level_id>/comparisons/<type>', methods=['GET'])
@load_user
@load_org
def make_item_comparison(user, org, level, level_id, type):
    """
    Get all comparisons by level.
    """
    resp = get_item_comparison(org.id, org_id=org.id, level=level,
                               level_id=level_id, type=type, key='metrics')
    return jsonify(list(resp))


@bp.route('/api/v1/<level>/comparisons', methods=['GET'])
@load_user
@load_org
def get_comparisons(user, org, level):
    """
    Get all comparisons by level.
    """
    cr = get_comparison(org.id, level=level, type='all')
    return response_from_cache(cr)


@bp.route('/api/v1/<level>/comparisons', methods=['PUT'])
@load_user
@load_org
def refresh_comparisons(user, org, level):
    """
    Refresh content comparisons
    """
    refresh_comparison(org.id, level=level, type='all')
    return jsonify({'success': True})


@bp.route('/api/v1/<level>/comparisons/<type>', methods=['GET'])
@load_user
@load_org
def get_one_comparison(user, org, type, level):
    """
    Get one content comparison.
    """
    cr = get_comparison(org.id, level=level, type=type)
    return response_from_cache(cr)


@bp.route('/api/v1/<level>/comparisons/<type>', methods=['PUT'])
@load_user
@load_org
def refresh_one_comparison(user, org, type, level):
    """
    Refresh one content comparison.
    """
    refresh_comparison(org.id, level=level, type=type)
    return jsonify({'success': True})
