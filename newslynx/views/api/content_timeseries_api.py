import logging
import copy

from sqlalchemy import distinct
from flask import Blueprint

from newslynx.core import db
from newslynx.views.decorators import load_user, load_org
from newslynx.exc import NotFoundError
from newslynx.models import ContentItem
from newslynx.lib.serialize import jsonify
from newslynx.views.util import request_data, url_for_job_status
from newslynx.tasks import load
from newslynx.tasks.query_metric import QueryContentMetricTimeseries
from newslynx.models.relations import (
    content_items_events,
    content_items_tags,
    content_items_authors,
    events_tags
)
from newslynx.views.util import (
    arg_list, request_ts
)

# blueprint
bp = Blueprint('content_metrics', __name__)

log = logging.getLogger(__name__)


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
    has_filter = False  # we use this to keep track of whether
    # a filter has been applied.

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

    # include impact tags
    if len(incl_im_ids):
        has_filter = True
        res = db.session\
            .query(distinct(content_items_events.c.content_item_id))\
            .outerjoin(events_tags, events_tags.c.event_id == content_items_events.c.event_id)\
            .filter(events_tags.c.tag_id.in_(incl_im_ids))\
            .all()
        for r in res:
            if r[0] not in cids:
                cids.append(r[0])

    # exclude impact tags
    if len(excl_im_ids):
        has_filter = True
        res = db.session\
            .query(distinct(content_items_events.c.content_item_id))\
            .outerjoin(events_tags, events_tags.c.event_id == content_items_events.c.event_id)\
            .filter(~events_tags.c.tag_id.in_(incl_im_ids))\
            .all()
        for r in res:
            if r[0] in all_cids:
                all_cids.remove(r[0])

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
        group_by_id=True
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
    kw = request_ts(unit='hour')
    q = QueryContentMetricTimeseries(org, [content_item_id], **kw)
    return jsonify(list(q.execute()))


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
