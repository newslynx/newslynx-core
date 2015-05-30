from gevent.pool import Pool

from sqlalchemy import or_

from newslynx.core import db
from newslynx.lib import url
from newslynx import settings
from newslynx.models import url_cache, Event, Thing, Tag
from newslynx.exc import RequestError
from newslynx.models.util import (
    split_meta, get_table_columns,
    fetch_by_id_or_field)


# a pool to multithread url_cache.
url_extract_pool = Pool(settings.URL_CACHE_POOL_SIZE)


def extract_urls(obj, fields):
    """
    Extract and normalize urls from text/html fields in an object.
    """
    urls = set()
    for f in fields:
        v = obj.get(f)
        if v:
            for u in url.from_html(v):
                if u not in urls:
                    urls.add(u)
                    yield u

            for u in url.from_string(v):
                if u not in urls:
                    urls.add(u)
                    yield u


def event(raw_obj,
          url_fields=['title', 'text', 'description'],
          requires=['source_id', 'org_id', 'title', 'text']):

        # get event columns.
    cols = [
        c for c in get_table_columns(Event)
        if c not in ['meta', 'tags']
    ]

    # check required fields
    for k in requires:
        if k not in raw_obj:
            raise RequestError(
                "Missing '{}'. An Event Requires {}".format(k, requires))

    # get org_id
    org_id = raw_obj.get('org_id')

    # check for tags:
    tag_ids = raw_obj.pop('tag_ids', [])
    thing_ids = raw_obj.pop('thing_ids', [])

    # check for author(s) + normalize as list.
    if 'author' in raw_obj:
        raw_obj['authors'] = raw_obj.pop('author')

    if 'authors' in raw_obj:
        if not isinstance(raw_obj['authors'], list):
            raw_obj['authors'] = [raw_obj['authors']]

    # if there are tags, the status is approved
    if len(tag_ids):
        raw_obj['status'] = 'approved'

    # normalize the url
    if raw_obj.get('url'):
        raw_obj['url'] = url_cache.get(raw_obj['url'])

    # enforce source_id as string
    raw_obj['source_id'] = str(raw_obj['source_id'])

    # split out meta fields
    raw_obj = split_meta(raw_obj, cols)
    print raw_obj

    e = Event.query\
        .filter_by(org_id=org_id)\
        .filter_by(source_id=raw_obj['source_id'])\
        .first()

    # create event
    if not e:

        # create event
        e = Event(**raw_obj)

    # update it
    else:
        for k, v in raw_obj.items():
            setattr(e, k, v)

    # extract urls in pool
    raw_urls = list(extract_urls(raw_obj, fields=url_fields))

    clean_urls = []
    for u in url_extract_pool.imap_unordered(url_cache.get, raw_urls):
        clean_urls.append(u)

    # detect things
    if len(clean_urls):

        things = Thing.query\
            .filter(or_(Thing.url.in_(clean_urls), Thing.id.in_(thing_ids)))\
            .filter(Thing.org_id == org_id)\
            .all()

        # create association.
        for t in things:
            if t.id not in e.thing_ids:
                e.things.append(t)

    # add tags
    for tid in tag_ids:
        tag = fetch_by_id_or_field(Tag, 'slug', tid, org_id)
        if tag:
            if tag.id not in e.tag_ids:
                e.tags.append(tag)

    db.session.add(e)
    db.session.commit()
    return e


def thing(raw_obj,
          url_fields=['title', 'text', 'description'],
          requires=['source_id', 'org_id', 'title', 'text']):

    # get event columns.
    cols = [
        c for c in get_table_columns(Event)
        if c not in ['meta']
    ]

    # check required fields
    for k in requires:
        if k not in raw_obj:
            raise RequestError(
                "Missing '{}'. An Event Requires {}".format(k, requires))

    # split out meta fields
    raw_obj = split_meta(raw_obj, cols)
    print raw_obj

    # get org_id
    org_id = raw_obj.get('org_id')

    # check for tags:
    tag_ids = raw_obj.pop('tag_ids', [])
    thing_ids = raw_obj.pop('thing_ids', [])

    # if there are tags, the status is approved
    if len(tag_ids):
        raw_obj['status'] = 'approved'

    # normalize the url
    if raw_obj.get('url'):
        raw_obj['url'] = url_cache.get(raw_obj['url'])

    # enforce source_id as string
    raw_obj['source_id'] = str(raw_obj['source_id'])

    e = Event.query\
        .filter_by(org_id=org_id)\
        .filter_by(source_id=raw_obj['source_id'])\
        .first()

    # create event
    if not e:

        # create event
        e = Event(**raw_obj)

    # update it
    else:
        for k, v in raw_obj.items():
            setattr(e, k, v)

    # extract urls in pool
    raw_urls = list(extract_urls(raw_obj, fields=url_fields))

    clean_urls = []
    for u in url_extract_pool.imap_unordered(url_cache.get, raw_urls):
        clean_urls.append(u)

    # detect things
    if len(clean_urls):

        things = Thing.query\
            .filter(or_(Thing.url.in_(clean_urls), Thing.id.in_(thing_ids)))\
            .filter(Thing.org_id == org_id)\
            .all()

        # create association.
        for t in things:
            if t.id not in e.thing_ids:
                e.things.append(t)

    # add tags
    for tid in tag_ids:
        tag = fetch_by_id_or_field(Tag, 'slug', tid, org_id)
        if tag:
            if tag.id not in e.tag_ids:
                e.tags.append(tag)

    db.session.add(e)
    db.session.commit()
    return e
