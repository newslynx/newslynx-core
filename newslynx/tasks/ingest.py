from gevent.pool import Pool

from sqlalchemy import or_

from newslynx.core import db
from newslynx import settings
from newslynx.models import (
    url_cache, Event, Thing, Tag,
    Recipe)
from newslynx.exc import RequestError
from newslynx.models.util import (
    split_meta, get_table_columns,
    fetch_by_id_or_field)
from newslynx.util import gen_uuid
from newslynx.views.util import (
    validate_thing_types, validate_event_status)
from newslynx.lib import dates
from newslynx.lib import url
from newslynx.lib import text
from newslynx.lib import html
from newslynx.lib import article


# a pool to multithread url_cache.
url_extract_pool = Pool(settings.URL_CACHE_POOL_SIZE)

EXTRACTORS = {
    'article': article.extract
}


def event(o,
          url_fields=['title', 'content', 'description'],
          requires=['org_id', 'content'],
          only_things=False):
    """
    Ingest an Event.
    """

    # check required fields
    _check_requires(o, requires, type='Event')

    # keep track if we detected things
    has_things = False

    # get org_id
    org_id = o.get('org_id')

    # validate status
    if 'status' in o:
        validate_event_status(o['status'])

    # normalize the url
    o['url'] = _prepare_url(o, 'url')

    # sanitize creation date
    o['created'] = _prepare_date(o, 'created')

    # sanitize text/html fields
    o['title'] = _prepare_str(o, 'title')
    o['description'] = _prepare_str(o, 'description')
    o['content'] = _prepare_str(o, 'content', o['url'])

    # split out tags_ids + thing_ids
    tag_ids = o.pop('tag_ids', [])
    thing_ids = o.pop('thing_ids', [])

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
        for k, v in o.items():
            setattr(e, k, v)
        e.updated = dates.now()

    # extract urls asynchronously.
    urls = _extract_urls(o, url_fields, source=o.get('url'))
    
    print urls
    
    # detect things
    if len(urls):
        print urls
        things = Thing.query\
            .filter(or_(Thing.url.in_(urls), Thing.id.in_(thing_ids)))\
            .filter(Thing.org_id == org_id)\
            .all()

        if len(things):
            has_things = True

            # upsert things.
            for t in things:
                if t.id not in e.thing_ids:
                    e.things.append(t)

    # associate tags
    if len(tag_ids):
        for tid in tag_ids:
            tag = fetch_by_id_or_field(Tag, 'slug', tid, org_id)
            if not tag:
                raise RequestError(
                    'Tag with id/slug {} does not exist.'.format(tid))
            if tag:
                if tag.type != 'impact':
                    raise RequestError(
                        'Only impact tags can be associated with Events. '
                        'Tag {} is of type {}'.format(tag.id, tag.type))

            # if there are tags, the status is approved
            e.status = 'approved'

            # upsert
            if tag.id not in e.tag_ids:
                e.tags.append(tag)

    # dont commit event if we're only looking
    # for events that link to things
    if not has_things and only_things:
        return

    db.session.add(e)
    db.session.commit()
    return e


def _extract_urls(obj, fields, source=None):
    """
    Extract, normalize, and dedupe urls from
    text/html fields in an object.
    """
    raw_urls = set()
    for f in fields:
        v = obj.get(f)
        if v:
            v = str(v)
            print "V", v
            if html.is_html(v):
                for u in url.from_html(v, source):
                    print "HERE"
                    print u
                    raw_urls.add(u)
            else:
                for u in url.from_string(v, source):
                    raw_urls.add(u)

    clean_urls = set()
    for u in url_extract_pool.imap_unordered(url_cache.get, list(raw_urls)):
        clean_urls.add(u)
    return list(clean_urls)


def _prepare_str(o, field, source_url=None):
    """
    Prepare text/html fi_streld
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
        raise RequestError(' {}: {} is an invalid date.'
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
                "Missing '{}'. An {} Requires {}".format(k, type, requires))


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
    if 'recipe_id' not in o:
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
            raise RequestError('Recipe id "{recipe_id}" does not exist.'
                               .format(**o))

        # reformant source id.
        o['source_id'] = "{}:{}"\
            .format(r.sous_chef.slug, str(o['source_id']))

        # set this event as non-manual
        o['provenance'] = 'recipe'

    return o
