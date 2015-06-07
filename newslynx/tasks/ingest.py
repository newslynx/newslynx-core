from gevent.pool import Pool

from sqlalchemy import or_

from newslynx.core import db
from newslynx import settings
from newslynx.util import gen_uuid
from newslynx.lib import dates
from newslynx.lib import url
from newslynx.lib import text
from newslynx.lib import html
from newslynx.lib import article
from newslynx.models import (
    url_cache, Event, ContentItem, Tag,
    Recipe)
from newslynx.models.util import (
    split_meta, get_table_columns,
    fetch_by_id_or_field)
from newslynx.views.util import (
    validate_content_item_types, validate_event_status)
from newslynx.exc import RequestError, UnprocessableEntityError

# a pool to multithread url_cache.
url_cache_pool = Pool(settings.URL_CACHE_POOL_SIZE)


def event(o,
          org_id,
          url_fields=['title', 'body', 'description'],
          requires=['title'],
          must_link=False):
    """
    Ingest an Event.
    """

    # check required fields
    _check_requires(o, requires, type='Event')

    # keep track if we detected content_items
    has_content_items = False

    # check if the org_id is in the body
    # TODO: I don't think this is necessary.
    org_id = o.pop('org_id', org_id)

    # get rid of ``id`` if it somehow got in here.
    o.pop('id', None)

    # validate status
    if 'status' in o:
        validate_event_status(o['status'])
        if o['status'] == 'deleted':
            raise RequestError(
                'You cannot create an Event with status "deleted."')

    # normalize the url
    o['url'] = _prepare_url(o, 'url')

    # sanitize creation date
    o['created'] = _prepare_date(o, 'created')

    # sanitize text/html fields
    o['title'] = _prepare_str(o, 'title', o['url'])
    o['description'] = _prepare_str(o, 'description', o['url'])
    o['body'] = _prepare_str(o, 'body', o['url'])

    # split out tags_ids + content_item_ids
    tag_ids = o.pop('tag_ids', [])
    content_item_ids = o.pop('content_item_ids', [])
    links = o.pop('links', [])

    # determine event provenance
    o = _event_provenance(o, org_id)

    # split out meta fields
    o = split_meta(o, get_table_columns(Event))

    # see if the event already exists.
    e = Event.query\
        .filter_by(org_id=org_id)\
        .filter_by(source_id=o['source_id'])\
        .first()

    # if not, create it
    if not e:

        # create event
        e = Event(**o)

    # else, update it
    else:
        # if it's deleted, issue a message.
        if e.status == 'deleted':
            raise UnprocessableEntityError(
                'Event {} already exists and has been previously deleted.'
                .format(e.id))

        for k, v in o.items():
            setattr(e, k, v)
        e.updated = dates.now()

    # extract urls asynchronously.
    urls = _extract_urls(o, url_fields, source=o.get('url'), links=links)

    # detect content_items
    if len(urls):
        content_items = ContentItem.query\
            .filter(or_(ContentItem.url.in_(urls),
                        ContentItem.id.in_(content_item_ids)))\
            .filter(ContentItem.org_id == org_id)\
            .all()

        if len(content_items):
            has_content_items = True

            # upsert content_items.
            for t in content_items:
                if t.id not in e.content_item_ids:
                    e.content_items.append(t)

    # associate tags
    if len(tag_ids):
        for tid in tag_ids:
            tag = fetch_by_id_or_field(Tag, 'slug', tid, org_id)
            if not tag:
                raise RequestError(
                    'Tag with id/slug {} does not exist.'
                    .format(tid))

            if tag:
                if tag.type != 'impact':
                    raise RequestError(
                        'Only impact tags can be associated with Events. '
                        'Tag {} is of type {}'
                        .format(tag.id, tag.type))

            # if there are tags, the status is approved
            e.status = 'approved'

            # upsert
            if tag.id not in e.tag_ids:
                e.tags.append(tag)

    # dont commit event if we're only looking
    # for events that link to content_items
    if not has_content_items and must_link:
        return None

    db.session.add(e)
    db.session.commit()
    return e


def _extract_urls(obj, fields, source=None, links=[]):
    """
    Extract, normalize, and dedupe urls from
    text/html fields in an object.
    """
    raw_urls = set(links)
    for f in fields:
        v = obj.get(f)
        if v:
            for u in url.from_any(str(v), source=source):
                raw_urls.add(u)

    clean_urls = set()
    for u in url_cache_pool.imap_unordered(url_cache.get, list(raw_urls)):
        clean_urls.add(u)
    return list(clean_urls)


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
    dt = dates.parse_any(o[field])
    if not dt:
        raise RequestError(
            '{}: {} is an invalid date.'
            .format(field, o[field]))
    return dt


def _prepare_url(o, field):
    """
    Prepare a url
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    return url_cache.get(o[field])


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


def _event_provenance(o, org_id):
    """
    if there's not a recipe_id set a random source id +
    set the recipe_id as "None" and preface the source_id
    as "manual".

    if there is recipe_id, add in the
    sous-chef-name to ensure that there
    aren't duplicate events generated by
    multiple child recipes of the same
    sous-chef
    """

    if 'recipe_id' not in o or not o['recipe_id']:
        o['source_id'] = "manual:{}".format(gen_uuid())
        o['provenance'] = 'manual'
        o['recipe_id'] = None

    else:
        # recipe-generated events must pass in a source id
        if 'source_id' not in o:
            raise RequestError(
                'Recipe-generated events must include a source_id.')

        # fetch the associated recipe
        r = Recipe.query\
            .filter_by(id=o['recipe_id'])\
            .filter_by(org_id=org_id)\
            .first()

        if not r:
            raise RequestError(
                'Recipe id "{recipe_id}" does not exist.'
                .format(**o))

        # reformant source id.
        o['source_id'] = "{}:{}"\
            .format(str(r.slug), str(o['source_id']))

        # set this event as non-manual
        o['provenance'] = 'recipe'

    return o
