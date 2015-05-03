from flask import Blueprint
from sqlalchemy import func, desc, asc
from pprint import pprint

from newslynx.core import db
from newslynx.exc import RequestError
from newslynx.models import Event, Tag, Task, Recipe, Thing
from newslynx.models.relations import events_tags, things_events
from newslynx.models.util import get_table_columns
from newslynx.lib.serialize import jsonify
from newslynx.lib import dates
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import *


# blueprint
bp = Blueprint('events', __name__)


# utils


def apply_event_filters(q, **kw):
    """
    Given a base Event.query, apply all filters.
    """

    # filter by organization_id
    q = q.filter(Event.organization_id == kw['org'])

    # apply search query
    if kw['search_query']:
        if kw['sort_field'] == 'relevance':
            sort = True
        else:
            sort = False
        q = q.search(kw['search_query'], sort=sort)

    # apply status filter
    if kw['status'] != 'all':
        q = q.filter(Event.status == kw['status'])

    # apply date filters
    if kw['created_after']:
        q = q.filter(Event.created >= kw['created_after'])
    if kw['created_before']:
        q = q.filter(Event.created <= kw['created_before'])
    if kw['updated_after']:
        q = q.filter(Event.updated >= kw['updated_after'])
    if kw['updated_before']:
        q = q.filter(Event.updated <= kw['updated_before'])

    # apply recipe filter
    if len(kw['include_recipes']):
        q = q.filter(Event.recipe_id.in_(kw['include_recipes']))
    if len(kw['exclude_recipes']):
        q = q.filter(~Event.recipe_id.in_(kw['exclude_recipes']))

    # apply tag categories/levels filter
    # TODO don't use multiple queries here.
    if len(kw['include_categories']):
        tag_ids = db.session.query(Tag.id).filter_by(organization_id=kw['org'])\
            .filter(Tag.category.in_(kw['include_categories']))\
            .all()
        tag_ids = [t[0] for t in tag_ids]
        pprint(tag_ids)
        q = q.filter(Event.tags.any(Tag.id.in_(tag_ids)))

    if len(kw['exclude_categories']):
        tag_ids = db.session.query(Tag.id).filter_by(organization_id=kw['org'])\
            .filter(Tag.category.in_(kw['exclude_categories']))\
            .all()
        tag_ids = [t[0] for t in tag_ids]
        pprint(tag_ids)
        q = q.filter(~Event.tags.any(Tag.id.in_(tag_ids)))

    if len(kw['include_levels']):
        tag_ids = db.session.query(Tag.id).filter_by(organization_id=kw['org'])\
            .filter(Tag.level.in_(kw['include_levels']))\
            .all()
        tag_ids = [t[0] for t in tag_ids]
        pprint(tag_ids)
        q = q.filter(Event.tags.any(Tag.id.in_(tag_ids)))

    if len(kw['exclude_levels']):
        tag_ids = db.session.query(Tag.id).filter_by(organization_id=kw['org'])\
            .filter(Tag.level.in_(kw['exclude_levels']))\
            .all()
        tag_ids = [t[0] for t in tag_ids]
        pprint(tag_ids)
        q = q.filter(~Event.tags.any(Tag.id.in_(tag_ids)))

    # apply tags filter
    if len(kw['include_tags']):
        q = q.filter(Event.tags.any(Tag.id.in_(kw['include_tags'])))
    if len(kw['exclude_tags']):
        q = q.filter(~Event.tags.any(Tag.id.in_(kw['exclude_tags'])))

    # apply things filter
    if len(kw['include_things']):
        q = q.filter(Event.things.any(Thing.id.in_(kw['include_things'])))
    if len(kw['exclude_things']):
        q = q.filter(~Event.things.any(Thing.id.in_(kw['exclude_things'])))

    # apply tasks filter
    # TODO: DONT USE MULTIPLE QUERIES HERE
    if len(kw['include_tasks']):
        task_recipes = db.session.query(Recipe.id)\
            .filter(Recipe.task.has(Task.name.in_(kw['include_tasks'])))
        q = q.filter(Event.recipe_id.in_([r[0] for r in task_recipes.all()]))

    if len(kw['exclude_tasks']):
        task_recipes = db.session.query(Recipe.id)\
            .filter(Recipe.task.has(Task.name.in_(kw['exclude_tasks'])))\
            .all()
        q = q.filter(~Event.recipe_id.in_([r[0] for r in task_recipes]))

    return q


# endpoints


@bp.route('/api/v1/events', methods=['GET'])
@load_user
@load_org
def search_events(user, org):
    """
    args:
        q              | search query
        fields         | a comma-separated list of fields to include in response
        page           | page number
        per_page       | number of items per page.
        sort           | variable to order by, preface with '-' to sort desc.
        created_after  | isodate variable to filter results after
        created_before | isodate variable to filter results before
        updated_after  | isodate variable to filter results after
        updated_before | isodate variable to filter results before
        status         | ['pending', 'approved', 'deleted']
        facets         | a comma-separated list of facets to include, default=all
        tag            | a comma-separated list of tags to filter by
        categories     | a comma-separated list of tag_categories to filter by
        levels         | a comma-separated list of tag_levels to filter by
        tag_ids        | a comma-separated list of thing_ids to filter by
        thing_ids      | a comma-separated list of thing_ids to filter by
        recipe_ids     | a comma-separated list of recipes to filter by
    """

    # parse arguments

    # store raw kwargs for generating pagination urls..
    raw_kw = dict(request.args.items())
    raw_kw['apikey'] = user.apikey
    raw_kw['org'] = org.id

    # special arg tuples
    sort_field, direction = \
        arg_sort('sort', default='-created')
    include_tags, exclude_tags = \
        arg_list('tag_ids', default=[], typ=int, exclusions=True)
    include_things, exclude_things = \
        arg_list('thing_ids', default=[], typ=int, exclusions=True)
    include_recipes, exclude_recipes = \
        arg_list('recipe_ids', default=[], typ=int, exclusions=True)
    include_tasks, exclude_tasks = \
        arg_list('tasks', default=[], typ=str, exclusions=True)
    include_levels, exclude_levels = \
        arg_list('levels', default=[], typ=str, exclusions=True)
    include_categories, exclude_categories = \
        arg_list('categories', default=[], typ=str, exclusions=True)

    kw = dict(
        search_query=arg_str('q', default=None),
        fields=arg_list('fields', default=None),
        page=arg_int('page', default=1),
        per_page=arg_limit('per_page'),
        sort_field=sort_field,
        direction=direction,
        created_after=arg_date('created_after', default=None),
        created_before=arg_date('created_before', default=None),
        updated_after=arg_date('updated_after', default=None),
        updated_before=arg_date('updated_before', default=None),
        status=arg_str('status', default='all'),
        facets=arg_list('facets', default=[], typ=str),
        include_categories=include_categories,
        exclude_categories=exclude_categories,
        include_levels=include_levels,
        exclude_levels=exclude_levels,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
        include_things=include_things,
        exclude_things=exclude_things,
        include_recipes=include_recipes,
        exclude_recipes=exclude_recipes,
        include_tasks=include_tasks,
        exclude_tasks=exclude_tasks,
        apikey=user.apikey,
        org=org.id
    )

    # validate arguments

    # validate sort fields are part of Event object.
    if kw['sort_field'] and kw['sort_field'] != 'relevance':
        validate_fields(Event, [kw['sort_field']], 'to sort by')

    # validate select fields.
    if kw['fields']:
        validate_fields(Event, kw['fields'], 'to select by')

    validate_tag_categories(kw['include_categories'])
    validate_tag_categories(kw['exclude_categories'])
    validate_tag_levels(kw['include_levels'])
    validate_tag_levels(kw['exclude_levels'])
    validate_event_status(kw['status'])
    validate_event_facets(kw['facets'])

    # base query
    event_query = Event.query

    # apply filters
    event_query = apply_event_filters(event_query, **kw)

    # select event fields
    if kw['fields']:
        columns = [eval('Event.{}'.format(f)) for f in kw['fields']]
        event_query = event_query.with_entities(*columns)

    # apply sort if we havent already sorted by query relevance.
    if kw['sort_field'] != 'relevance':
        sort_obj = eval('Event.{sort_field}.{direction}'.format(**kw))
        event_query = event_query.order_by(sort_obj())

    if len(kw['facets']):

        facets = {}

        # get all event ids for computing counts
        filter_entities = event_query.with_entities(Event.id).all()
        event_ids = [f[0] for f in filter_entities]

        # excecute count queries
        # TODO: INTEGRATE WITH CELERY

        # events by recipes
        if 'recipes' in kw['facets'] or 'all' in kw['facets']:
            recipe_counts = db.session\
                .query(Event.recipe_id, Recipe.name, func.count(Recipe.id))\
                .join(Recipe)\
                .filter(Event.id.in_(event_ids))\
                .order_by(desc(func.count(Recipe.id)))\
                .group_by(Event.recipe_id, Recipe.name).all()
            facets['recipes'] = [dict(zip(['id', 'name', 'count'], r))
                                 for r in recipe_counts]

        # events by tag
        if 'tags' in kw['facets'] or 'all' in kw['facets']:
            tag_counts = db.session\
                .query(Tag.id, Tag.name, Tag.type, Tag.level, Tag.category, Tag.color, func.count(Tag.id))\
                .outerjoin(events_tags)\
                .filter(events_tags.c.event_id.in_(event_ids))\
                .order_by(desc(func.count(Tag.id)))\
                .group_by(Tag.id, Tag.name, Tag.type, Tag.level, Tag.category, Tag.color)\
                .all()
            facets['tags'] = [dict(zip(['id', 'name', 'type', 'level', 'category', 'color', 'count'], c))
                              for c in tag_counts]

        # events by tag category
        if 'categories' in kw['facets'] or 'all' in kw['facets']:
            category_counts = db.session\
                .query(Tag.category, func.count(Tag.category))\
                .outerjoin(events_tags)\
                .filter(events_tags.c.event_id.in_(event_ids))\
                .order_by(desc(func.count(Tag.category)))\
                .group_by(Tag.category).all()
            facets['categories'] = [dict(zip(['category', 'count'], c))
                                    for c in category_counts]

        # events by level
        if 'levels' in kw['facets'] or 'all' in kw['facets']:
            level_counts = db.session\
                .query(Tag.level, func.count(Tag.level))\
                .outerjoin(events_tags)\
                .filter(events_tags.c.event_id.in_(event_ids))\
                .order_by(desc(func.count(Tag.level)))\
                .group_by(Tag.level).all()
            facets['levels'] = [dict(zip(['level', 'count'], c))
                                for c in level_counts]

        # events by task
        if 'tasks' in kw['facets'] or 'all' in kw['facets']:
            task_counts = db.session\
                .query(Task.name, func.count(Task.name))\
                .join(Recipe)\
                .join(Event)\
                .filter(Event.id.in_(event_ids))\
                .order_by(desc(func.count(Task.name)))\
                .group_by(Task.name)
            facets['tasks'] = [dict(zip(['name', 'count'], c))
                               for c in task_counts.all()]

        # events by things
        if 'things' in kw['facets'] or 'all' in kw['facets']:
            thing_counts = db.session\
                .query(Thing.id, Thing.url, Thing.title, func.count(Thing.id))\
                .filter(Thing.events.any(Event.id.in_(event_ids)))\
                .order_by(desc(func.count(Thing.id)))\
                .group_by(Thing.id, Thing.url, Thing.title).all()
            facets['things'] = [dict(zip(['id', 'url', 'title', 'count'], c))
                                for c in thing_counts]

        # events by things
        if 'statuses' in kw['facets'] or 'all' in kw['facets']:
            status_counts = db.session\
                .query(Event.status, func.count(Event.status))\
                .filter(Event.id.in_(event_ids))\
                .order_by(desc(func.count(Event.status)))\
                .group_by(Event.status).all()
            facets['statuses'] = [dict(zip(['id', 'url', 'title', 'count'], c))
                                  for c in status_counts]

    # paginate event_query
    events = event_query\
        .paginate(kw['page'], kw['per_page'], False)

    # total results
    total = events.total

    # generate pagination urls
    pagination = \
        urls_for_pagination('events.search_events', total, **raw_kw)

    # reformat entites as dictionary
    if kw['fields']:
        events = [dict(zip(kw['fields'], r)) for r in events.items]
    else:
        events = events.items

    resp = {
        'results': events,
        'pagination': pagination,
        'total': total
    }

    if len(kw['facets']):
        resp['facets'] = facets

    return jsonify(resp)


@bp.route('/api/v1/events/<int:event_id>', methods=['GET'])
@load_user
@load_org
def event(user, org, event_id):
    """
    Fetch an individual event.
    """
    e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
    if not e:
        raise RequestError(
            'An Event with ID {} does not exist.'.format(event_id))
    return jsonify(e)


@bp.route('/api/v1/events/<int:event_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def event_update(user, org, event_id):
    """
    Modify an individual event.
    """
    e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
    if not e:
        raise RequestError(
            'An Event with ID {} does not exist.'.format(event_id))

    # get request data
    req_data = request_data()

    # fetch tag and thing
    tag_ids = listify_data_arg('tag_ids')
    thing_ids = listify_data_arg('thing_ids')

    # check for current status / PUT status
    current_status = e.status
    req_status = req_data.get('status')

    if len(tag_ids) and len(thing_ids):

        approve = True
        tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
        if not len(tags):
            raise RequestError(
                'Tag(s) with ID(s) {} do(es) not exist.'.format(tag_ids))

        things = Thing.query.filter(Thing.id.in_(thing_ids)).all()
        if not len(things):
            raise RequestError(
                'Thing(s) with ID(s) {} do(es) not exist.'.format(tag_ids))

    # check for incomplete approval requests.
    elif current_status != 'approved' and req_status == 'approved':

        raise RequestError(
            'To approve an event you must assign it to one or more '
            'Things or Tags by using the "thing_ids" and "tag_ids" fields.')

    else:
        approve = False

    # filter out any non-columns
    columns = get_table_columns(Event)
    for k in req_data.keys():
        if k not in columns:
            req_data.pop(k)

    # if we're approving this event, override status
    if approve:
        req_data['status'] = 'approved'

    # add "updated" dat
    req_data['updated'] = dates.now()

    # update fields
    for k, v in req_data.items():
        setattr(e, k, v)

    # ensure no one sneakily/accidentally
    # updates an organization id
    e.organization_id = org.id

    # if we're approving, add tags + things
    if approve:

        # only add things + tags that haven't already been assigned.
        for thing, tag in zip(things, tags):
            if thing.id not in e.thing_ids:
                e.things.append(thing)

            # validate tag
            if tag.type != 'impact':
                raise RequestError('Events can only be assigned Impact Tags.')

            # add it
            if tag.id not in e.tag_ids:
                e.tags.append(tag)

    # commit changes
    db.session.add(e)
    db.session.commit()

    # return modified event
    return jsonify(e)


@bp.route('/api/v1/events/<int:event_id>', methods=['DELETE'])
@load_user
@load_org
def event_delete(user, org, event_id):
    """
    Delete an individual event. Here, we do not explicitly "delete"
    the event, but update it's status instead. This will help
    when polling recipes for new events since we'll be able to ensure
    that we do not create duplicate events.
    """
    e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
    if not e:
        raise RequestError(
            'An Event with ID {} does not exist.'.format(event_id))

    # remove associations
    # from
    # http://stackoverflow.com/questions/9882358/how-to-delete-rows-from-a-table-using-an-sqlalchemy-query-without-orm
    d = events_tags.delete(events_tags.c.event_id == event_id)
    db.session.execute(d)

    d = things_events.delete(things_events.c.event_id == event_id)
    db.session.execute(d)

    # update event
    e.status = 'deleted'
    e.updated = dates.now()

    # add object
    db.session.add(e)
    db.session.commit()

    # return modified event
    return jsonify(e)


@bp.route('/api/v1/events/<int:event_id>/tags/<int:tag_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def event_add_tag(user, org, event_id, tag_id):
    """
    Add a tag to an event.
    """
    e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
    if not e:
        raise RequestError(
            'An Event with ID {} does not exist.'.format(event_id))

    if not e.status == 'approved':
        raise RequestError(
            'You must first approve an Event before adding additional Tags.')

    tag = Tag.query.filter_by(id=tag_id, organization_id=org.id).first()
    if not tag:
        raise RequestError(
            'Tag with ID {} does not exist.'.format(tag_id))

    print(tag.to_dict())
    if tag.type != 'impact':
        raise RequestError('Events can only be assigned Impact Tags.')

    if tag.id not in e.tag_ids:
        e.tags.append(tag)

    e.updated = dates.now()
    db.session.add(e)
    db.session.commit()

    # return modified event
    return jsonify(e)


@bp.route('/api/v1/events/<int:event_id>/tags/<int:tag_id>', methods=['DELETE'])
@load_user
@load_org
def event_delete_tag(user, org, event_id, tag_id):
    """
    Add a tag to an event.
    """
    e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
    if not e:
        raise RequestError(
            'An Event with ID {} does not exist.'.format(event_id))

    if tag_id not in e.tag_ids:
        raise RequestError(
            'An Event with ID {} does not currently have an association '
            'with a Tag with ID {}'.format(event_id, tag_id))

    for tag in e.tags:
        if tag.id == tag_id:
            e.tags.remove(tag)

    e.updated = dates.now()
    db.session.add(e)
    db.session.commit()

    # return modified event
    return jsonify(e)


@bp.route('/api/v1/events/<int:event_id>/things/<int:thing_id>', methods=['PUT'])
@load_user
@load_org
def event_add_thing(user, org, event_id, thing_id):
    """
    Add a tag to an event.
    """
    e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
    if not e:
        raise RequestError(
            'An Event with ID {} does not exist.'.format(event_id))

    if not e.status == 'approved':
        raise RequestError(
            'You must first approve an Event before adding additional Things.')

    thing = Thing.query.filter_by(id=thing_id, organization_id=org.id).first()
    if not thing:
        raise RequestError(
            'Thing with ID {} does not exist.'.format(thing_id))

    if thing.id not in e.thing_ids:
        e.things.append(thing)

    e.updated = dates.now()
    db.session.add(e)
    db.session.commit()

    # return modified event
    return jsonify(e)


@bp.route('/api/v1/events/<int:event_id>/things/<int:thing_id>', methods=['DELETE'])
@load_user
@load_org
def event_delete_thing(user, org, event_id, thing_id):
    """
    Add a tag to an event.
    """
    e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
    if not e:
        raise RequestError(
            'An Event with ID {} does not exist.'.format(event_id))

    if thing_id not in e.thing_ids:
        raise RequestError(
            'An Event with ID {} does not currently have an association '
            'with a Thing with ID {}'.format(event_id, thing_id))

    for thing in e.things:
        if thing.id == thing_id:
            e.things.remove(thing)

    e.updated = dates.now()
    db.session.add(e)
    db.session.commit()

    # return modified event
    return jsonify(e)
