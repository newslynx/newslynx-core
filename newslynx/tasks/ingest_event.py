from sqlalchemy import or_

from newslynx.core import gen_session
from newslynx.util import gen_uuid
from newslynx.models import (
    Event, ContentItem, Tag, Recipe)
from newslynx.models.util import get_table_columns
from newslynx.views.util import validate_event_status
from newslynx.exc import RequestError, UnprocessableEntityError
from newslynx.tasks import ingest_util


def ingest(
        obj,
        org_id,
        org_domains,
        requires=['title'],
        must_link=False,
        kill_session=True):
    """
    Ingest an Event.
    """

    # distinct session for this eventlet.
    session = gen_session()

    has_content_items = False

    # check required fields
    ingest_util.check_requires(obj, requires, type='Event')

    # validate status
    if 'status' in obj:
        validate_event_status(obj['status'])
        if obj['status'] == 'deleted':
            raise RequestError(
                'You cannot create an Event with status of "deleted."')

    # check if the org_id is in the body
    # TODO: I don't think this is necessary.
    org_id = obj.pop('org_id', org_id)

    # get rid of ``id`` if it somehow got in here.
    obj.pop('id', None)

    # normalize the url
    obj['url'] = ingest_util.prepare_url(obj, 'url')

    # sanitize creation date
    obj['created'] = ingest_util.prepare_date(obj, 'created')
    if not obj['created']:
        obj.pop('created')

    # sanitize text/html fields
    obj['title'] = ingest_util.prepare_str(obj, 'title', obj['url'])
    obj['description'] = ingest_util.prepare_str(
        obj, 'description', obj['url'])
    obj['body'] = ingest_util.prepare_str(obj, 'body', obj['url'])

    # get thumbnail
    obj['thumbnail'] = ingest_util.prepare_thumbnail(obj, 'img_url')

    # split out tags_ids + content_item_ids + links
    tag_ids = obj.pop('tag_ids', [])
    content_item_ids = obj.pop('content_item_ids', [])
    links = obj.pop('links', [])

    # determine event provenance
    obj = _event_provenance(obj, org_id, session)

    # split out meta fields
    obj = ingest_util.split_meta(obj, get_table_columns(Event))

    # see if the event already exists.
    e = session.query(Event)\
        .filter_by(org_id=org_id)\
        .filter_by(source_id=obj['source_id'])\
        .first()

    # if not, create it
    if not e:

        # create event
        e = Event(org_id=org_id, **obj)

    # else, update it
    else:
        # if it's deleted, issue a message.
        if e.status == 'deleted':
            raise UnprocessableEntityError(
                'Event {} already exists and has been previously deleted.'
                .format(e.id))

        for k, v in obj.items():
            setattr(e, k, v)

    # extract urls and normalize urls asynchronously.
    links = ingest_util.prepare_links(links, org_domains)

    # detect content_items
    if len(links) or len(content_item_ids):
        e, has_content_items = _associate_content_items(
            e, org_id, links, content_item_ids, session)

    # associate tags
    if len(tag_ids):
        e = _associate_tags(e, org_id, tag_ids, session)

    # dont commit event if we're only looking
    # for events that link to content_items
    if not has_content_items and must_link:
        return None

    session.add(e)
    session.commit()
    if kill_session:
        session.close()
    return e


def _event_provenance(o, org_id, session):
    """
    if there's not a recipe_id set a random source id +
    set the recipe_id as "None" and preface the source_id
    as "manual".

    if there is recipe_id, add in the
    reciple-slug to ensure that there
    aren't duplicate events generated by
    multiple the same recipe.
    """

    if 'recipe_id' not in o or not o['recipe_id']:
        o['source_id'] = "manual:{}".format(gen_uuid())
        o['provenance'] = 'manual'
        o['recipe_id'] = None

    else:
        # recipe-generated events must pass in a source id
        if 'source_id' not in o:
            raise RequestError(
                'Recipe generated events must include a source_id.')

        # fetch the associated recipe
        r = session.query(Recipe)\
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


def _associate_content_items(e, org_id, urls, content_item_ids, session):
    """
    Check if event has associations with content items.
    """
    has_content_items = False

    content_items = session.query(ContentItem)\
        .filter(or_(ContentItem.url.in_(urls),
                    ContentItem.id.in_(content_item_ids)))\
        .filter(ContentItem.org_id == org_id)\
        .all()

    if len(content_items):
        has_content_items = True

        # upsert content_items.
        for c in content_items:
            if c.id not in e.content_item_ids:
                e.content_items.append(c)
    return e, has_content_items


def _associate_tags(e, org_id, tag_ids, session):
    """
    Associate tags with event ids.
    """
    if not isinstance(tag_ids, list):
        tag_ids = [tag_ids]

    for tag in tag_ids:

        # is this an id or a name ?
        try:
            int(tag)
            is_name = False

        except ValueError:
            is_name = True

        # upsert by name.
        if is_name:

            # standardize as much as we can.
            t = session.query(Tag)\
                .filter_by(slug=tag, org_id=org_id)\
                .first()

        # upsert by id.
        else:
            t = session.query(Tag)\
                .filter_by(id=tag, org_id=org_id)\
                .first()

        # create new author.
        if not t:
            raise RequestError(
                'A tag with ID/slug "{}" does not exist'
                .format(tag))

        # upsert associations
        if t.id not in e.tag_ids:
            e.tags.append(t)
    return e
