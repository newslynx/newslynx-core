import logging
import copy
from datetime import timedelta

from flask import Blueprint

from newslynx.core import db
from newslynx.views.decorators import load_user, load_org
from newslynx.exc import NotFoundError, RequestError, InternalServerError
from newslynx.models import ContentItem
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data, url_for_job_status
from newslynx.tasks import load
from newslynx.lib import dates
from newslynx.tasks import rollup_metric
from newslynx.constants import CONTENT_METRIC_COMPARISONS
from newslynx.tasks.query_metric import QueryContentMetricTimeseries
from newslynx.models import (
    ComparisonsCache, AllContentComparisonCache,
    SubjectTagsComparisonCache,
    ContentTypeComparisonCache,
    ImpactTagsComparisonCache,
    Event, Tag, Author)
from newslynx.models.relations import (
    content_items_events,
    content_items_tags,
    content_items_authors
)
from newslynx.constants import (
    NULL_VALUES,
)

from newslynx.settings import (
    METRICS_CONTENT_LIST_TIMESERIES_DAYS
)

from newslynx.views.util import (
    arg_bool, arg_str, validate_ts_unit, arg_list,
    arg_date, arg_int, delete_response
)

# blueprint
bp = Blueprint('content_metrics', __name__)

log = logging.getLogger(__name__)

comparisons_cache = ComparisonsCache()
comparison_types = {
    'all': AllContentComparisonCache(),
    'impact_tags': ImpactTagsComparisonCache(),
    'subject_tags': SubjectTagsComparisonCache(),
    'types': ContentTypeComparisonCache()
}


def request_ts(**d):
    """
    A helper for parsing timeseries query strings.
    """
    # set defaults
    d.setdefault('unit', 'hour')
    d.setdefault('sparse', True)
    d.setdefault('sig_digits', 2)
    d.setdefault('group_by_id', True)
    d.setdefault('select', ['*'])
    d.setdefault('time_since_start', False)
    d.setdefault('rm_nulls', False)
    d.setdefault('transform', None)
    d.setdefault('before', None)
    d.setdefault('after', None)

    # select / exclude
    select, exclude = arg_list(
        'select', typ=str, exclusions=True, default=d['select'])
    if '*' in select:
        exclude = []
        select = "*"

    # parse query kwargs.
    kw = dict(
        unit=arg_str('unit', default=d['unit']),
        sparse=arg_bool('sparse', default=d['sparse']),
        sig_digits=arg_int('sig_digits', default=d['sig_digits']),
        group_by_id=arg_bool('group_by_id', default=d['group_by_id']),
        select=select,
        exclude=exclude,
        rm_nulls=arg_bool('rm_nulls', default=d['rm_nulls']),
        time_since_start=arg_bool('time_since_start', default=d['time_since_start']),
        transform=arg_str('transform', default=d['transform']),
        before=arg_date('before', default=d['before']),
        after=arg_date('after', default=d['after'])
    )
    # check for null here.
    if kw['unit'] in NULL_VALUES:
        kw['unit'] = None
    return kw


@bp.route('/api/v1/content/timeseries', methods=['GET'])
@load_user
@load_org
def list_content_timeseries(user, org):
    """
    Query the content timeseries for an entire org.
    """
    # query content by:
    incl_cids, excl_cids = \
        arg_list('ids', typ=int, exclusions=True, default=['all'])
    incl_author_ids, excl_author_ids = \
        arg_list('author_ids', typ=int, exclusions=True, default=[])
    incl_st_ids, excl_st_ids = \
        arg_list('subject_tag_ids', typ=int, exclusions=True, default=[])
    incl_im_ids, excl_im_ids = \
        arg_list('impact_tag_ids', typ=int, exclusions=True, default=[])
    incl_event_ids, excl_event_ids = \
        arg_list('event_ids', typ=int, exclusions=True, default=[])
    has_filter = False

    # get all cids
    all_cids = copy.copy(org.content_item_ids)

    # add in cids
    cids = []

    # include authors
    if len(incl_author_ids):
        has_filter = True
        res = db.session.query(content_items_authors.c.content_item_id)\
            .filter(content_items_authors.c.author_id.in_(incl_author_ids))\
            .all()
        for r in res:
            if r[0] not in cids:
                cids.append(r[0])

    # exclude authors
    if len(excl_author_ids):
        has_filter = True
        res = db.session.query(content_items_authors.c.content_item_id)\
            .filter(~content_items_authors.c.author_id.in_(excl_author_ids))\
            .all()
        for r in res:
            if r[0] in all_cids:
                all_cids.remove(r[0])

    # include subject tags
    if len(incl_st_ids):
        has_filter = True
        res = db.session.query(content_items_tags.c.content_item_id)\
            .filter(content_items_tags.c.tag_id.in_(incl_st_ids))\
            .all()
        for r in res:
            if r[0] not in cids:
                cids.append(r[0])

    # exclude subject tags
    if len(excl_st_ids):
        has_filter = True
        res = db.session.query(content_items_tags.c.content_item_id)\
            .filter(~content_items_tags.c.tag_id.in_(excl_st_ids))\
            .all()
        for r in res:
            if r[0] in all_cids:
                all_cids.remove(r[0])

    # include events
    if len(incl_event_ids):
        has_filter = True
        res = db.session.query(content_items_events.c.content_item_id)\
            .filter(content_items_events.c.event_id.in_(incl_event_ids))\
            .all()
        for r in res:
            if r[0] not in cids:
                cids.append(r[0])

    # exclude events
    if len(excl_event_ids):
        has_filter = True
        res = db.session.query(content_items_events.c.content_item_id)\
            .filter(~content_items_events.c.event_id.in_(incl_event_ids))\
            .all()
        for r in res:
            if r[0] in all_cids:
                all_cids.remove(r[0])

    # # include impact tags
    # if len(incl_im_ids):
    #     has_filter = True
    #     res = db.session.query(content_items_tags.c.content_item_id)\
    #         .filter(content_items_tags.c.tag_id.in_(incl_im_ids))\
    #         .all()
    #     for r in res:
    #         if r[0] not in cids:
    #             cids.append(r[0])

    # # exclude impact tags
    # if len(excl_im_ids):
    #     has_filter = True
    #     res = db.session.query(content_items_tags.c.content_item_id)\
    #         .filter(~content_items_tags.c.tag_id.in_(excl_im_ids))\
    #         .all()
    #     for r in res:
    #         if r[0] in all_cids:
    #             all_cids.remove(r[0])

    # remove exlucde cids:
    for c in cids:
        if c not in all_cids:
            cids.remove(c)

    if has_filter and not len(cids):
        raise NotFoundError(
            'Could not find Content Item Ids that matched the input parameters'
        )

    elif not has_filter and not len(cids):
        if 'all' in incl_cids:
            cids.extend(all_cids)
        else:
            has_filter = True
            cids.extend(incl_cids)
        # remove cids
        if not 'all' in excl_cids:
            has_filter = True
            for c in excl_cids:
                all_cids.remove(c)

    # execute the query.
    kw = request_ts(
        unit='day',
        group_by_id=True,
        after=dates.now() - timedelta(METRICS_CONTENT_LIST_TIMESERIES_DAYS)
    )
    q = QueryContentMetricTimeseries(org,  cids, **kw)
    return jsonify(list(q.execute()))


@bp.route('/api/v1/content/<content_item_id>/timeseries', methods=['GET'])
@load_user
@load_org
def get_content_timeseries(user, org, content_item_id):
    """
    Query an individual content timeseries.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id)\
        .filter_by(org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'A ContentItem with ID {} does not exist'
            .format(content_item_id))

    # select / exclude
    select, exclude = arg_list(
        'select', typ=str, exclusions=True, default=['*'])
    if '*' in select:
        exclude = []
        select = "*"

    kw = dict(
        unit=arg_str('unit', default='hour'),
        sparse=arg_bool('sparse', default=True),
        sig_digits=arg_int('sig_digits', default=2),
        select=select,
        exclude=exclude,
        rm_nulls=arg_bool('rm_nulls', default=False),
        time_since_start=arg_bool('time_since_start', default=False),
        transform=arg_str('transform', default=None),
        before=arg_date('before', default=None),
        after=arg_date('after', default=None)
    )

    q = QueryContentMetricTimeseries(org, [content_item_id], **kw)
    return jsonify(q.execute())


@bp.route('/api/v1/content/<content_item_id>/timeseries', methods=['POST'])
@load_user
@load_org
def create_content_item_timeseries(user, org, content_item_id):
    """
    Upsert content timseries metrics.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id)\
        .filter_by(org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'A ContentItem with ID {} does not exist'
            .format(content_item_id))

    # insert content item id
    req_data = request_data()
    if not isinstance(req_data, list):
        req_data = [req_data]
    data = []
    for row in req_data:
        row.update({'content_item_id': c.id})
        data.append(row)

   # load.
    ret = load.content_timeseries(
        data,
        org_id=org.id,
        metrics_lookup=org.content_timeseries_metrics,
        content_item_ids=[content_item_id],
        queue=False)

    return jsonify(ret)


@bp.route('/api/v1/content/timeseries/bulk', methods=['POST'])
@load_user
@load_org
def bulk_create_content_timeseries(user, org):
    """
    bulk upsert timseries metrics for an organization's content items.
    """
    # bulk load in a queue
    job_id = load.content_timeseries(
        request_data(),
        org_id=org.id,
        metrics_lookup=org.content_timeseries_metrics,
        content_item_ids=org.content_item_ids,
        queue=True)

    ret = url_for_job_status(apikey=user.apikey, job_id=job_id, queue='bulk')
    return jsonify(ret, status=202)


@bp.route('/api/v1/content/<content_item_id>/summary', methods=['POST'])
@load_user
@load_org
def content_metrics_summary(user, org, content_item_id):
    """
    upsert summary metrics for a content_item.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id)\
        .filter_by(org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'A ContentItem with ID {} does not exist'
            .format(content_item_id))

    req_data = request_data()

    # check for valid format.
    if not isinstance(req_data, dict):
        raise RequestError(
            "Non-bulk endpoints require a single json object."
        )

    # insert content item id
    req_data['content_item_id'] = content_item_id

    ret = load.content_summary(
        req_data,
        org_id=org.id,
        metrics_lookup=org.content_summary_metrics,
        content_item_ids=org.content_item_ids,
        commit=True
    )
    return jsonify(ret)


@bp.route('/api/v1/content/summary/bulk', methods=['POST'])
@load_user
@load_org
def bulk_create_content_summary(user, org):
    """
    bulk upsert summary metrics for an organization's content items.
    """
    req_data = request_data()

    # check for valid format.
    if not isinstance(req_data, list):
        raise RequestError(
            "Bulk endpoints require a list of json objects."
        )

    # check for content_item_id.
    if not 'content_item_id' in req_data[0].keys():
        raise RequestError(
            'You must pass in a content_item_id with each record.')

    job_id = load.content_summary(
        req_data,
        org_id=org.id,
        metrics_lookup=org.content_summary_metrics,
        content_item_ids=org.content_item_ids,
        commit=False)

    ret = url_for_job_status(apikey=user.apikey, job_id=job_id, queue='bulk')
    return jsonify(ret, status=202)


@bp.route('/api/v1/content/summary', methods=['PUT'])
@load_user
@load_org
def refresh_content_summary(user, org):
    """
    Refresh content summary metrics
    """
    since = arg_int('since', 24)
    rollup_metric.content_timeseries_to_summary(org, [], since)
    rollup_metric.event_tags_to_summary(org)
    return jsonify({'success': True})


@bp.route('/api/v1/content/comparisons', methods=['GET'])
@load_user
@load_org
def get_all_content_comparisons(user, org):
    """
    Refresh content comparisons.
    """
    refresh = arg_bool('refresh', default=False)
    cache_details = arg_bool('cache_details', default=False)
    if refresh:
        comparisons_cache.invalidate(org.id)
    cr = comparisons_cache.get(org.id)
    if refresh and cr.is_cached:
        raise InternalServerError(
            'Something went wrong with the cache invalidation process.')
    if cache_details:
        return jsonify({'cache': cr, 'comparisons': cr.value})
    return jsonify(cr.value)


@bp.route('/api/v1/content/comparisons', methods=['PUT'])
@load_user
@load_org
def refresh_content_comparisons(user, org):
    """
    Refresh content comparisons
    """
    comparisons_cache.invalidate(org.id)
    cr = comparisons_cache.get(org.id)
    if not cr.is_cached:
        return jsonify({'success': True})
    raise InternalServerError(
        'Something went wrong with the comparison cache invalidation process.')


@bp.route('/api/v1/content/comparisons/<type>', methods=['GET'])
@load_user
@load_org
def get_one_content_comparisons(user, org, type):
    """
    Get one content comparison.
    """
    # allow the urls to be pretty slugs :)
    type = type.replace('-', "_")
    if type not in CONTENT_METRIC_COMPARISONS:
        raise RequestError(
            "'{}' is an invalid content metric comparison. Choose from {}"
            .format(type, ", ".join(CONTENT_METRIC_COMPARISONS)))
    refresh = arg_bool('refresh', default=False)
    cache_details = arg_bool('cache_details', default=False)
    if refresh:
        comparison_types[type].invalidate(org.id)
    cr = comparison_types[type].get(org.id)
    if refresh and cr.is_cached:
        raise InternalServerError(
            'Something went wrong with the comparison cache invalidation process.')
    if cache_details:
        return jsonify({'cache': cr, 'comparison': cr.value.get(type)})
    return jsonify(cr.value.get(type))


@bp.route('/api/v1/content/comparisons/<type>', methods=['PUT'])
@load_user
@load_org
def refresh_one_content_comparisons(user, org, type):
    """
    Get one content comparison.
    """
    type = type.replace('-', "_")
    if type not in CONTENT_METRIC_COMPARISONS:
        raise RequestError(
            "'{}' is an invalid content metric comparison. Choose from {}"
            .format(type, ", ".join(CONTENT_METRIC_COMPARISONS)))
    comparison_types[type].invalidate(org.id)
    cr = comparison_types[type].get(org.id)
    if not cr.is_cached:
        return jsonify({'success': True})
    raise InternalServerError(
        'Something went wrong with the comparison cache invalidation process.')
