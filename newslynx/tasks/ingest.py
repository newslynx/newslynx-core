"""
The messy work of making unstructured data structured.
Upserting all the things since 2015.

We want ingestion to decrease the amount of labor involved in
writing Sous Chefs. As a result we adhere to the following principles:

1. Everything should work as an upsert.
2. Fields should be exhaustively stanadardized.
3. Relations between entities should be automatically established.
4. This all works quickly, reliably, and concurrently when possible.

As a result we've written a mess of spaghetti code to enforce these principles.
This file is the dark side of Merlynne.

"""

import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.pool import Pool

import logging
from functools import partial
from datetime import datetime

from newslynx.core import db
from newslynx.util import gen_uuid
from newslynx.models import Recipe, Event, ContentItem, Author
from newslynx.models import URLCache, ThumbnailCache, ExtractCache
from newslynx.models.util import get_table_columns, fetch_by_id_or_field
from newslynx.exc import RequestError
from newslynx.tasks.util import ResultIter
from newslynx.util import uniq
from newslynx.lib import dates
from newslynx.lib import stats
from newslynx.lib import url
from newslynx.lib import text
from newslynx.lib import html
from newslynx.lib import author
from newslynx.lib.serialize import obj_to_json
from newslynx.core import settings
from newslynx.constants import (
    METRIC_FACET_KEYS, EVENT_STATUSES,
    CONTENT_ITEM_TYPES)

log = logging.getLogger(__name__)


# the url cache object
url_cache = URLCache()
thumbnail_cache = ThumbnailCache()
extract_cache = ExtractCache()

# a pool to multithread url_cache.
url_cache_pool = Pool(settings.URL_CACHE_POOL_SIZE)


def source(data, **kw):
    """
    Single interface for bulkloaders.
    Structured this way to aid pickling.
    """
    src = kw.pop('src', None)
    if not src:
        raise ValueError('Missing src.')
    fx = {
        'events': events,
        'content': content,
        'content_timeseries': content_timeseries,
        'content_summary': content_summary,
        'org_timeseries': org_timeseries,
        'org_summary': org_summary
    }
    if not fx.get(src):
        raise Exception('No ingest source named "{}" exists'.format(src))
    return fx.get(src)(data, **kw)


def events(data, **kw):
    """
    Ingest Events. Steps:
    1. Clean input data.
    2. Prepare links
    3. Lookup Content Items
    4. Lookup Tags
    5. Check for duplicates
    6. Perform last three tasks in parallel.
    7. Upsert all events. Ignore events without links when the must_link flag is added.
    8. Upsert all associations. Ignore events without ids because of step above.
    """

    # parse kwargs.s
    org_id = kw.get('org_id')
    recipe_id = kw.get('recipe_id', -9999)
    org_domains = kw.get('org_domains', [])
    queued = kw.get('queued', False)
    requires = kw.get('requires', ['title'])
    must_link = kw.get('must_link', False)

    # pool
    p = Pool(20)

    # standardized format.
    if not isinstance(data, list):
        data = [data]

    # fetch recipe
    recipe = fetch_by_id_or_field(Recipe, 'slug', recipe_id,  org_id=org_id)

    # create ingest objects
    events = {}
    meta = {}

    # STEP 1: Clean data:

    def _clean():
        __prepare = partial(
            _prepare, requires=requires, recipe=recipe, org_id=org_id, type='event')
        for obj in p.imap_unordered(__prepare, data):
            # split out tags_ids + content_item_ids + links
            meta[obj['source_id']] = dict(
                tag_ids=obj.pop('tag_ids', obj.pop('tags', [])),
                content_item_ids=obj.pop('content_item_ids', []),
                links=obj.pop('links', [])
            )
            # split out meta fields
            obj = _split_meta(obj, get_table_columns(Event))

            # add to lookup
            events[obj['source_id']] = obj

    # STEP 2: Prepare links.

    def _links():

        links = [(k, l) for k, v in meta.iteritems() for l in v['links']]

        # function for cleaning urls.
        def _link(args):
            source_id, l = args
            l = _prepare_url(
                {'l': l}, field='l', expand=True, canonicalize=True)
            if l:
                if not len(org_domains):
                    return source_id, l
                if any([d in l for d in org_domains]):
                    return source_id, l
            return None, None

        # clean urls asynchronously.
        for source_id, link in p.imap_unordered(_link, links):
            if source_id:
                if not 'links' in meta[source_id]:
                    meta[source_id]['links'] = []
                if source_id and link not in meta[source_id]['links']:
                    meta[source_id]['links'].append(link)

    # these need to happen synchronously
    _clean()
    _links()

    # STEP 3: LOOKUP CONTENT ITEM IDS.
    # Here we generate one query to lookup all ids
    # rather than hundreds of queries per id.
    def _content_items():
        content_query = """
        SELECT '{}' AS source_id, id FROM content
        WHERE (url in ({}) or id in ({}))
        AND org_id = {}
        """
        queries = []
        for source_id, vals in meta.iteritems():
            links = ",".join(
                ["'%s'" % l for l in uniq(meta[source_id].pop('links', []))])
            ids = ",".join(
                [str(i) for i in uniq(meta[source_id].pop('content_item_ids', []))])
            if len(links) or len(ids):

                # THIS IS KIND OF A HACK FOR NOW.
                if not links:
                    links = "'__null___'"
                if not ids:
                    ids = '-99999'
                queries.append(
                    content_query.format(source_id, links, ids, org_id))

        # execute query + modify meta.
        if len(queries):
            q = " UNION ALL ".join(queries)
            for row in ResultIter(db.session.execute(q)):
                src_id = row['source_id']
                k = 'content_item_ids'
                if k not in meta[src_id]:
                    meta[src_id][k] = []
                meta[src_id][k].append(row['id'])
        db.session.commit()
        db.session.close()
        db.session.remove()


    # STEP 4: LOOKUP TAG IDS
    def _tags():
        tag_query = """
        SELECT '{}' AS source_id, id FROM tags
        WHERE (slug in ({}) or id in ({}))
        AND org_id = {} AND type='impact'
        """

        queries = []
        for source_id, vals in meta.iteritems():
            if not source_id:
                continue
            # separate slugs and ids.
            tags = uniq(meta[source_id].pop('tag_ids', []))
            ids = []
            slugs = []
            for t in tags:
                try:
                    ids.append(int(t))
                except ValueError:
                    slugs.append(t)
            slugs = ",".join(["'%s'" % s for s in slugs])
            ids = ",".join([str(i) for i in ids])
            if len(slugs) or len(ids):
                if not slugs:
                    slugs = "'__null___'"
                if not ids:
                    ids = '-99999'
                queries.append(tag_query.format(source_id, slugs, ids, org_id))

        # execute query + modify meta.
        if len(queries):
            q = "\nUNION ALL\n".join(queries)
            for row in ResultIter(db.session.execute(q)):
                src_id = row['source_id']
                k = 'tag_ids'
                if k not in meta[src_id]:
                    meta[src_id][k] = []
                meta[src_id][k].append(row['id'])
        db.session.commit()
        db.session.close()
        db.session.remove()


    # STEP 5 Check for duplicate events.

    def _dupes():
        # list of source ids.
        source_ids = ",".join(["'%s'" % s for s in events.keys()])

        dupe_query = \
            """SELECT source_id, status
               FROM events
               WHERE source_id IN ({}) AND org_id = {}
            """.format(source_ids, org_id)

        for row in ResultIter(db.session.execute(dupe_query)):
            if not meta[row['source_id']].get('exists', None):
                # ignore events that have been previously deleted
                status = row['status']
                if status == 'deleted':
                    events.pop(row['source_id'], None)
                    break

                # keep track of ones that exist.
                meta[row['source_id']]['exists'] = True
        db.session.commit()
        db.session.close()
        db.session.remove()


     # STEP 6 Perform reconcilation steps in parallel.
    def _reconcile():
        # execute reconciliation tasks in parallel.
        tasks = []
        for t in [_dupes, _tags, _content_items]:
            tasks.append(gevent.spawn(t))
        gevent.joinall(tasks)

    _reconcile()

    # Step 7: Create/Update events
    def _upsert_events():

        # disambiguate
        to_create = {}
        to_update = {}
        for id, e in events.iteritems():
            if meta[id].get('exists', False):
                to_update[id] = e
            else:
                to_create[id] = e

        # create objects
        for id, e in to_create.iteritems():
            events[id] = Event(**e)

        # update query
        existing = Event.query\
            .filter(Event.source_id.in_(to_update.keys()))\
            .all()

        for e in existing:
            for k, v in to_update[e.source_id].items():
                if k not in ['source_id', 'id', 'org_id', 'recipe_id']:
                    setattr(e, k, v)
            events[e.source_id] = e

        # commit
        for id, e in events.iteritems():
            # filter out events that don't link.
            if must_link and len(meta[id].get('content_item_ids', [])):
                db.session.add(e)
            if not must_link:
                db.session.add(e)
        db.session.commit()

    # upsert the events
    _upsert_events()

    # Step 8: Upsert Associations.

    def _assc():
        tag_args = []
        ci_args = []
        for src_id, e in events.iteritems():
            # only add associations for events that will be created.
            if not e.id:
                continue
            for tag_id in meta[src_id].get('tag_ids', []):
                tag_args.append((e.id, tag_id))
            for cid in meta[src_id].get('content_item_ids', []):
                ci_args.append((e.id, cid))

        _upsert_associations('upsert_events_tags', tag_args)
        _upsert_associations('upsert_content_items_events', ci_args)

    _assc()
    db.session.commit()
    # just return true for the queue.
    if queued:
        ret = True
    else:
        ret = [e.to_dict() for e in events.values()]
    db.session.close()
    db.session.remove()
    return ret


########################################

# Content items.

########################################


def content(data, **kw):
    """
    Ingest content. Steps:
    1. Clean input data.
    2. Reconcile Tags
    3. Reconcile / Upsert Authors.
    4. Check for duplicates
    5. Perform last three tasks in parallel.
    6. Upsert all content items.
    7. Upsert all associations.
    """

    # parse kwargs.
    org_id = kw.get('org_id')
    recipe_id = kw.get('recipe_id', -9999)
    queued = kw.get('queued', False)
    requires = kw.get('requires', ['url', 'type'])

    # distinct session for this eventlet.
    p = Pool(20)

    # standardized format.
    if not isinstance(data, list):
        data = [data]

    # fetch recipe
    recipe = fetch_by_id_or_field(Recipe, 'slug', recipe_id,  org_id=org_id)

    # create ingest objects
    cis = {}
    meta = {}

    # STEP 1: Clean data:

    def _clean():
        __prepare = partial(_prepare, requires=requires, recipe=recipe,
                            org_id=org_id, type='content_item',
                            extract=kw.get('extract', True))
        for obj in p.imap_unordered(__prepare, data):

            # determine unique id.
            uniqkey = "{}||{}".format(obj['url'], obj['type'])

            # set metadata.
            meta[uniqkey] = dict(
                author_ids=obj.pop('author_ids', obj.pop('authors', [])),
                tag_ids=obj.pop('tag_ids', obj.pop('tags', [])),
                links=obj.pop('links', []),
            )
            # split out meta fields
            obj = _split_meta(obj, get_table_columns(ContentItem))
            cis[uniqkey] = obj

    # this needs to happen syncnhronously.
    _clean()

    # Step 2: Lookup Tags
    # TODO: These queries should be more intelligently structured
    # They should be capable of looking up a tag only once and then
    # reassociate this tag with all associated source ids.
    # Currently, it replicates this query for every source id.
    def _tags():
        tag_query = """
        SELECT '{0}' AS uniqkey, id FROM tags
        WHERE (slug in ({1}) or id in ({2}))
        AND org_id = {3} AND type='subject'
        """
        queries = []
        for uniqkey, vals in meta.iteritems():

            # separate slugs and ids.
            tags = uniq(meta[uniqkey].pop('tag_ids', []))
            ids = []
            slugs = []
            for t in tags:
                try:
                    ids.append(int(t))
                except ValueError:
                    slugs.append(t)

            # format queries.
            slugs = ",".join(["'%s'" % s for s in slugs])
            ids = ",".join([str(i) for i in ids])
            if len(slugs) or len(ids):
                if not slugs:
                    slugs = "'__null___'"
                if not ids:
                    ids = '-99999'
                queries.append(tag_query.format(uniqkey, slugs, ids, org_id))

        # execute query + modify meta.
        if len(queries):
            q = "\nUNION ALL\n".join(queries)
            for row in ResultIter(db.session.execute(q)):
                id = row['uniqkey']
                k = 'tag_ids'
                if k not in meta[id]:
                    meta[id][k] = []
                meta[id][k].append(row['id'])
        db.session.commit()
        db.session.close()
        db.session.remove()


    # Step 3: Upsert Authors
    def _authors():
        author_query = """
        SELECT '{0}' AS uniqkey, id FROM authors
        WHERE (name in ({1}) or id in ({2}))
        AND org_id = {3}
        """
        queries = []
        for uniqkey, vals in meta.iteritems():

            # separate slugs and ids.
            authors = meta[uniqkey].get('author_ids', [])
            ids = []
            names = []
            for a in authors:
                try:
                    ids.append(int(a))
                except ValueError:
                    names.append(a.upper().strip())

            names = ",".join(["'%s'" % n for n in uniq(names)])
            ids = ",".join([str(i) for i in uniq(ids)])
            if names or ids:
                if not names:
                    names = "'__null___'"
                if not ids:
                    ids = '-99999'
                queries.append(
                    author_query.format(uniqkey, names, ids, org_id))

        # execute query + modify meta.
        if len(queries):
            q = "\nUNION ALL\n".join(queries)
            for row in ResultIter(db.session.execute(q)):
                id = row['uniqkey']
                k = 'author_ids'
                if k in meta[id]:
                    meta[id][k] = []
                meta[id][k].append(row['id'])
                meta[id]['authors_exist'] = True

        # check for authors we should create.
        to_create = []
        for uniqkey, item in meta.iteritems():
            if item.get('authors_exist', False):
                continue
            for a in meta[uniqkey].pop('author_ids', []):
                if not isinstance(a, (basestring, str, unicode)):
                    continue
                to_create.append((uniqkey, org_id, a))

        # if we should create them, do so.
        if len(to_create):
            # create authors + keep track of content relations
            authors_to_ids = dict()
            seen = set()
            for uniqkey, oid, name in to_create:
                name = name.upper().strip()
                if name not in seen and name.lower().strip() not in author.BAD_TOKENS:
                    authors_to_ids[name] = {}
                    seen.add(name.upper().strip())
                    a = Author(org_id=oid, name=name)
                    db.session.add(a)
                    authors_to_ids[name]['obj'] = a

                # keep track of ALL ids assoicated with this author.
                if name in authors_to_ids:
                    if not 'ids' in authors_to_ids[name]:
                        authors_to_ids[name]['ids'] = []
                    authors_to_ids[name]['ids'].append(uniqkey)

            # create new authors so we
            # can access their IDs.
            db.session.commit()

            # set author ids back on content item meta
            for name, values in authors_to_ids.iteritems():
                ids = values.get('ids', [])
                obj = values.get('obj')
                k = 'author_ids'
                for uniqkey in ids:
                    if k not in meta[uniqkey]:
                        meta[uniqkey][k] = []
                    meta[uniqkey][k].append(obj.id)
        db.session.close()
        db.session.remove()


    # Step 4: Detect Duplicates.
    def _dupes():
        dupe_query = \
            """SELECT url || '||' || type as uniqkey
               FROM content
               WHERE url = '{}' AND type = '{}' AND org_id = {}
            """
        queries = []
        for uniqkey in cis.keys():
            url, type = uniqkey.split('||')
            queries.append(dupe_query.format(url, type, org_id))

        if len(queries):
            q = " UNION ALL ".join(queries)
            for row in ResultIter(db.session.execute(q)):
                if not meta[row['uniqkey']].get('exists', None):
                    # keep track of ones that exist.
                    meta[row['uniqkey']]['exists'] = True
        db.session.commit()
        db.session.close()
        db.session.remove()


    # Step 5: Perform reconcilation in parallel.
    def _reconcile():
        # execute reconciliation tasks in parallel.
        tasks = []
        for t in [_dupes, _tags, _authors]:
            tasks.append(gevent.spawn(t))
        gevent.joinall(tasks)

    _reconcile()
    # db.session.commit()

    # Step 6: Create/Update content items.
    def _upsert_content():

        # disambiguate
        to_create = {}
        to_update = {}
        for uniqkey, ci in cis.iteritems():
            if meta[uniqkey].get('exists', False):
                to_update[uniqkey] = ci
            else:
                to_create[uniqkey] = ci

        # create objects
        if len(to_create.keys()):
            for uniqkey, ci in to_create.iteritems():
                cis[uniqkey] = ContentItem(**ci)

        # update query
        update_ids = ",".join(["'%s'" % str(i) for i in to_update.keys()])
        if len(update_ids):
            existing = ContentItem.query\
                .filter("content.url || '||' || content.type in ({})".format(update_ids))\
                .filter_by(org_id=org_id)\
                .all()

            for ci in existing:
                for k, v in to_update[ci.uniqkey].items():
                    if k not in ['id', 'org_id', 'recipe_id']:
                        setattr(ci, k, v)
                cis[ci.uniqkey] = ci

        # commit
        for ci in cis.values():
            db.session.add(ci)
        db.session.commit()

    # perform the command
    _upsert_content()

    # Step 7: Upsert Associations.
    def _assc():
        tag_args = []
        author_args = []
        for uniqkey, ci in cis.iteritems():
            for tag_id in meta[uniqkey].get('tag_ids', []):
                tag_args.append((ci.id, tag_id))
            for aid in meta[uniqkey].get('author_ids', []):
                author_args.append((ci.id, aid))
        _upsert_associations('upsert_content_items_tags', tag_args)
        _upsert_associations('upsert_content_items_authors', author_args)
        db.session.commit()

    _assc()

    # just return true for the queue.
    if queued:
        ret = True
    else:
        ret = [c.to_dict() for c in cis.values()]
    db.session.close()
    db.session.remove()
    return ret


def _prepare(obj, requires=[], recipe=None, type='event', org_id=None, extract=True):
    """
    Prepare a content item or an event.
    """

    # check required fields
    _check_requires(obj, requires, type=type)

    # validate status
    if type == 'event':
        if 'status' in obj:
            if not obj.get('status', None) in EVENT_STATUSES:
                raise RequestError(
                    'Invalid event status: {status}'.format(**obj))
            if obj['status'] == 'deleted':
                raise RequestError(
                    'You cannot create an Event with status of "deleted."')

    # validate type
    if type == 'content_item':
        if not obj.get('type', None) in CONTENT_ITEM_TYPES:
            raise RequestError(
                'Invalid content item type: {type}'.format(**obj))

    # get rid of ``id`` if it somehow got in here.
    obj.pop('id', None)
    obj.pop('org_id', None)

    # normalize the url
    if type == 'event':
        obj['url'] = _prepare_url(obj, 'url', expand=True, canonicalize=False)

    elif type == 'content_item':
        obj['url'] = _prepare_url(obj, 'url', expand=True, canonicalize=True)

    # sanitize creation date
    obj['created'] = _prepare_date(obj, 'created')
    if not obj['created']:
        obj.pop('created')

    # sanitize text/html fields
    obj['title'] = _prepare_str(obj, 'title', obj['url'])
    obj['description'] = _prepare_str(
        obj, 'description', obj['url'])
    obj['body'] = _prepare_str(obj, 'body', obj['url'])

    # set org id
    obj['org_id'] = org_id

    # check img url
    if not url.validate(obj.get('img_url', None)):
        obj['img_url'] = None

    # determine provenance.
    obj = _provenance(obj, recipe, type)

    # if type is content items and we're extracting. do it.
    if type == 'content_item' and extract and obj.get('url', None):
        cr = extract_cache.get(obj.get('url'), type=obj.get('type', None))

        if not cr.value:
            extract_cache.invalidate(
                obj.get('url'), type=obj.get('type', None))
            pass

        # merge extracted data with object.
        else:
            # merge extracted authors.
            for k, v in cr.value.items():
                if not obj.get(k, None):
                    obj[k] = v
                # preference extracted data
                if k in ['description', 'body']:
                    obj[k] = v
                elif k == 'authors':
                    if not k in obj:
                        obj[k] = v
                    else:
                        for vv in v:
                            if vv not in obj[k]:
                                obj[k].append(vv)

            # swap bad images.
            tn = _prepare_thumbnail(obj, 'img_url')
            if not tn:
                img = cr.value.get('img_url', None)
                if img:
                    obj['img_url'] = img
                    obj['thumbnail'] = _prepare_thumbnail(obj, 'img_url')
            else:
                obj['thumbnail'] = tn
    else:
        obj['thumbnail'] = _prepare_thumbnail(obj, 'img_url')

    # set domain
    obj['domain'] = url.get_domain(obj['url'])

    # return prepped object
    return obj


def _provenance(obj, recipe, type='event'):
    """
    Determine provenance for events or content items.
    Handle source ids for events.
    """
    if not recipe:
        obj['provenance'] = 'manual'
        obj['recipe_id'] = None

        if type == 'event':
            src_id = obj.get('source_id')
            if not src_id:
                src_id = gen_uuid()
            obj['source_id'] = "manual:{}".format(src_id)

    else:
        if type == 'event':
            # recipe-generated events must pass in a source id
            if 'source_id' not in obj:
                raise RequestError(
                    'Recipe generated events must include a source_id.')
            # reformant source id.
            obj['source_id'] = "{}:{}"\
                .format(str(recipe.slug), str(obj['source_id']))
        obj['provenance'] = 'recipe'
        obj['recipe_id'] = recipe.id
    return obj


def _upsert_associations(cmd, ids):
    """
    Upsert asscications efficiently.
    """
    query = "SELECT {}({},{})"
    queries = []
    for from_id, to_id in ids:
        queries.append(query.format(cmd, from_id, to_id))
    if len(queries):
        q = "\nUNION ALL\n".join(queries)
        db.session.execute(q)


def _prepare_str(o, field, source_url=None):
    """
    Prepare text/html field
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    if html.is_html(o[field]):
        return html.prepare(o[field], source_url)
    return text.prepare(o[field])


def _prepare_date(o, field):
    """
    Prepare a date
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    if isinstance(o[field], datetime):
        return o[field]
    dt = dates.parse_any(o[field], enforce_tz=True)
    if not dt:
        raise RequestError(
            '{}: "{}" is an invalid date.'
            .format(field, o[field]))
    return dt


def _prepare_url(o, field, source=None, **kw):
    """
    Prepare a url
    """
    if field not in o:
        return None
    if o[field] is None:
        return None

    if kw.get('canonicalize', False):
        return url.prepare(o[field], source=source, **kw)

    # prepare urls before attempting cached request.
    u = url.prepare(o[field], source=source, expand=False, canonicalize=False)
    cache_response = url_cache.get(u)

    return cache_response.value


def _prepare_thumbnail(o, field):
    """
    Prepare a url
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    u = o[field]

    # create a thumbnail from an image.
    cache_response = thumbnail_cache.get(u)
    return cache_response.value


def _check_requires(o, requires, type='Event'):
    """
    Check for presence of required fields.
    """
    # check required fields
    for k in requires:
        if k not in o:
            raise RequestError(
                "Missing '{}'. An {} Requires {}"
                .format(k, type, requires))


def _split_meta(obj, cols):
    """
    Split out meta fields from core columns.
    """
    meta = obj.pop('meta', {})
    for k in obj.keys():
        if k not in cols:
            meta[k] = obj.pop(k)
    obj['meta'] = meta
    return obj

########################################

# Metrics

########################################

# TODO: DONT REPEAT YOURSELF. Write a Decorator.


def content_timeseries(data, **kw):

    # parse kwargs.
    org_id = kw.get('org_id')
    content_item_ids = kw.get('content_item_ids', [])
    metrics_lookup = kw.get('metrics_lookup', [])
    queued = kw.get('queued', False)

    # standardized format.
    if not isinstance(data, list):
        data = [data]

    queries = []
    objects = []
    for obj in data:
        cid = _check_content_item_id(obj, content_item_ids)
        metrics = _prepare_metrics(obj, metrics_lookup)

        cmd_kwargs = {
            "org_id": org_id,
            "content_item_id": cid,
            'datetime': _prepare_metric_date(obj)
        }
        # upsert command
        cmd = """SELECT upsert_content_metric_timeseries(
                    {org_id},
                    {content_item_id},
                    '{datetime}',
                    '{metrics}')
               """.format(metrics=obj_to_json(metrics), **cmd_kwargs)
        queries.append(cmd)

        # build up list of objects.
        cmd_kwargs['metrics'] = metrics
        objects.append(cmd_kwargs)

    # execute queries.
    if len(queries):
        q = " UNION ALL ".join(queries)
        db.session.execute(q)
        db.session.commit()
        db.session.remove()
    if queued:
        return True
    return objects


def content_summary(data, **kw):
    """
    Ingest content summary metrics.
    """
    # parse kwargs.
    org_id = kw.get('org_id')
    content_item_ids = kw.get('content_item_ids', [])
    metrics_lookup = kw.get('metrics_lookup', [])
    queued = kw.get('queued', False)

    queries = []
    objects = []

    # standardized format.
    if not isinstance(data, list):
        data = [data]

    for obj in data:
        cid = _check_content_item_id(obj, content_item_ids)
        cmd_kwargs = {
            "org_id": org_id,
            "content_item_id": cid
        }
        metrics = _prepare_metrics(obj, metrics_lookup)

        # upsert command
        cmd = """SELECT upsert_content_metric_summary(
                    {org_id},
                    {content_item_id},
                    '{metrics}')
               """.format(metrics=obj_to_json(metrics), **cmd_kwargs)
        queries.append(cmd)

        # build up list of objects.
        cmd_kwargs['metrics'] = metrics
        objects.append(cmd_kwargs)

    # execute queries.
    if len(queries):
        q = " UNION ALL ".join(queries)
        db.session.execute(q)
        db.session.commit()
        db.session.remove()
    if queued:
        return True
    return objects


def org_timeseries(data, **kw):
    """
    Ingest Timeseries Metrics for an organization.
    """

    # parse kwargs.
    org_id = kw.get('org_id')
    metrics_lookup = kw.get('metrics_lookup', [])
    queued = kw.get('queued', False)

    queries = []
    objects = []

    # standardized format.
    if not isinstance(data, list):
        data = [data]

    for obj in data:

        metrics = _prepare_metrics(obj, metrics_lookup)
        cmd_kwargs = {
            "org_id": org_id,
            'datetime': _prepare_metric_date(obj)
        }
        # upsert command
        cmd = \
            """SELECT upsert_org_metric_timeseries(
             {org_id},
            '{datetime}',
            '{metrics}')
        """.format(metrics=obj_to_json(metrics), **cmd_kwargs)
        queries.append(cmd)

        cmd_kwargs['metrics'] = metrics
        objects.append(cmd_kwargs)

    # execute queries.
    if len(queries):
        q = " UNION ALL ".join(queries)
        db.session.execute(q)
        db.session.commit()
        db.session.remove()

    if queued:
        return True
    return objects


def org_summary(data, **kw):
    """
    This exists for consistency.
    """
    # parse kwargs.
    org_id = kw.get('org_id')
    metrics_lookup = kw.get('metrics_lookup', [])
    queued = kw.get('queued', False)

    queries = []
    objects = []

    # standardized format.
    if not isinstance(data, list):
        data = [data]

    for obj in data:

        metrics = _prepare_metrics(obj, metrics_lookup)
        cmd_kwargs = {
            "org_id": org_id,
        }
        # upsert command
        cmd = \
            """SELECT upsert_org_metric_summary(
             {org_id},
            '{metrics}')
        """.format(metrics=obj_to_json(metrics), **cmd_kwargs)
        queries.append(cmd)

        cmd_kwargs['metrics'] = metrics
        objects.append(cmd_kwargs)

    # execute queries.
    if len(queries):
        q = " UNION ALL ".join(queries)
        db.session.execute(q)
        db.session.commit()
        db.session.remove()
    if queued:
        return True
    return objects


def _check_content_item_id(obj, content_item_ids):
    """
    Raise errors if content item is missing.
    """
    cid = obj.pop('content_item_id', None)
    if not cid:
        raise RequestError('Object is missing a "content_item_id"')
    if not cid in content_item_ids:
        raise RequestError(
            'Content Item with ID {} doesnt exist'.format(cid))
    return cid


def _prepare_metric_date(obj):
    """
    Round a metric to a configurable unit.
    """
    u = settings.METRICS_MIN_DATE_UNIT
    v = settings.METRICS_MIN_DATE_VALUE

    # set current time if no time exists.
    if 'datetime' not in obj:
        return dates.floor_now(unit=u, value=v).isoformat()

    ds = obj.pop('datetime')
    dt = dates.parse_iso(ds, enforce_tz=True)
    return dates.floor(dt, unit=u, value=v).isoformat()


def _prepare_metrics(obj, metrics_lookup):
    """
    Given a lookup of all metrics this object can contain,
    validate the object and prepare for ingest.
    """
    # check if metrics exist and are properly formatted.
    obj.update(obj.pop('metrics', {}))
    for k in obj.keys():
        if k == 'datetime':
            continue

        # fetch from lookup
        m = metrics_lookup.get(k)
        if not m:
            raise RequestError(
                "Metric '{}' does not exist at this level."
                .format(k))

        # validate facet formatting.
        if m['faceted'] and not isinstance(obj[k], list):
            raise RequestError(
                "Metric '{}' is faceted but was not passed in as a list."
                .format(k))

        if m['faceted'] and len(obj[k]) \
           and not set(obj[k][0].keys()) == set(METRIC_FACET_KEYS):
            raise RequestError(
                "Metric '{}' is faceted, but it\'s elements are not properly formatted. "
                "Each facet must be a dictionary of '{\"facet\":\"facet_name\", \"value\": 1234}"
                .format(k))

        # remove empty facets
        if m['faceted'] and not len(obj[k]):
            obj.pop(k)

        # parse numbers.
        if not m['faceted']:
            obj[k] = stats.parse_number(obj[k])

        # parse facet values.
        else:
            for i, v in enumerate(obj[k]):
                obj[k][i]['value'] = \
                    stats.parse_number(obj[k][i]['value'])

    return obj
