from pprint import pprint

from flask import Blueprint
from sqlalchemy import func, text, desc, asc

from newslynx.core import db
from newslynx.exc import RequestError
from newslynx.models import Event, Tag, Task, Recipe, Thing
from newslynx.models.relations import events_tags, things_events, things_tags
from newslynx.models.util import get_table_columns
from newslynx.lib.serialize import jsonify
from newslynx.lib import dates
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import *


# blueprint
bp = Blueprint('things', __name__)


# utils


# TODO: Generalize this with `apply_event_filters`
def apply_thing_filters(q, **kw):
    """
    Given a base Thing.query, apply all filters.
    """

    # filter by organization_id
    q = q.filter(Thing.organization_id == kw['org'])

    # use this for keeping track of
    # levels/categories events.
    all_event_ids = set()

    # apply search query
    if kw['search_query']:
        if kw['sort_field'] == 'relevance':
            sort = True
        else:
            sort = False
        q = q.search(kw['search_query'], sort=sort)

    # apply status filter
    if kw['type'] != 'all':
        q = q.filter(Thing.type == kw['type'])

    # filter url by regex
    if kw['url']:
        q = q.filter(text('things.url ~ :regex')).params(regex=kw['url'])

    # filter by domain
    if kw['domain']:
        q = q.filter(Thing.domain == kw['domain'])

    # apply date filters
    if kw['created_after']:
        q = q.filter(Thing.created >= kw['created_after'])
    if kw['created_before']:
        q = q.filter(Thing.created <= kw['created_before'])
    if kw['updated_after']:
        q = q.filter(Thing.updated >= kw['updated_after'])
    if kw['updated_before']:
        q = q.filter(Thing.updated <= kw['updated_before'])

    # apply recipe filter
    if len(kw['include_recipes']):
        q = q.filter(Thing.recipe_id.in_(kw['include_recipes']))

    if len(kw['exclude_recipes']):
        q = q.filter(~Thing.recipe_id.in_(kw['exclude_recipes']))

    # apply tag categories/levels filter
    # TODO try not to use multiple queries here.
    if len(kw['include_categories']):
        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(organization_id=kw['org'])\
            .filter(Tag.category.in_(kw['include_categories']))\
            .all()
        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            all_event_ids.add(e)
        q = q.filter(Thing.events.any(Event.id.in_(event_ids)))

    if len(kw['exclude_categories']):
        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(organization_id=kw['org'])\
            .filter(Tag.category.in_(kw['exclude_categories']))\
            .all()
        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            all_event_ids.remove(e)
        q = q.filter(Thing.events.any(Event.id.in_(event_ids)))

    if len(kw['include_levels']):
        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(organization_id=kw['org'])\
            .filter(Tag.level.in_(kw['include_levels']))\
            .all()
        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            all_event_ids.add(e)
        q = q.filter(Thing.events.any(Event.id.in_(event_ids)))

    if len(kw['exclude_levels']):
        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(organization_id=kw['org'])\
            .filter(Tag.level.in_(kw['exclude_levels']))\
            .all()
        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            all_event_ids.remove(e)
        q = q.filter(Thing.events.any(Event.id.in_(event_ids)))

    # apply tags filter
    if len(kw['include_tags']):
        q = q.filter(Thing.tags.any(Tag.id.in_(kw['include_tags'])))

    if len(kw['exclude_tags']):
        q = q.filter(~Thing.tags.any(Tag.id.in_(kw['exclude_tags'])))

    # apply tasks filter
    # TODO: DONT USE MULTIPLE QUERIES HERE
    if len(kw['include_tasks']):
        task_recipes = db.session.query(Recipe.id)\
            .filter(Recipe.task.has(Task.name.in_(kw['include_tasks'])))\
            .all()
        recipe_ids = [r[0] for r in task_recipes]
        q = q.filter(Thing.recipe_id.in_(recipe_ids))

    if len(kw['exclude_tasks']):
        task_recipes = db.session.query(Recipe.id)\
            .filter(Recipe.task.has(Task.name.in_(kw['exclude_tasks'])))\
            .all()
        recipe_ids = [r[0] for r in task_recipes]
        q = q.filter(~Thing.recipe_id.in_(recipe_ids))

    return q, list(all_event_ids)


# endpoints


@bp.route('/api/v1/things', methods=['GET'])
@load_user
@load_org
def search_things(user, org):
    """
    args:
        q              | search query
        url            | a regex for a url
        domain         | a domain to match on
        fields         | a comma-separated list of fields to include in response
        page           | page number
        per_page       | number of items per page.
        sort           | variable to order by, preface with '-' to sort desc.
        created_after  | isodate variable to filter results after
        created_before | isodate variable to filter results before
        updated_after  | isodate variable to filter results after
        updated_before | isodate variable to filter results before
        type           | ['pending', 'approved', 'deleted']
        facets         | a comma-separated list of facets to include, default=[]
        tag            | a comma-separated list of tags to filter by
        categories     | a comma-separated list of tag_categories to filter by
        levels         | a comma-separated list of tag_levels to filter by
        tag_ids        | a comma-separated list of thing_ids to filter by
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
        url=arg_str('url', default=None),
        domain=arg_str('domain', default=None),
        fields=arg_list('fields', default=None),
        page=arg_int('page', default=1),
        per_page=arg_limit('per_page'),
        sort_field=sort_field,
        direction=direction,
        created_after=arg_date('created_after', default=None),
        created_before=arg_date('created_before', default=None),
        updated_after=arg_date('updated_after', default=None),
        updated_before=arg_date('updated_before', default=None),
        type=arg_str('type', default='all'),
        facets=arg_list('facets', default=[], typ=str),
        include_categories=include_categories,
        exclude_categories=exclude_categories,
        include_levels=include_levels,
        exclude_levels=exclude_levels,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
        include_recipes=include_recipes,
        exclude_recipes=exclude_recipes,
        include_tasks=include_tasks,
        exclude_tasks=exclude_tasks,
        org=org.id
    )

    # validate arguments

    # validate sort fields are part of Event object.
    if kw['sort_field'] and kw['sort_field'] != 'relevance':
        validate_fields(Thing, [kw['sort_field']], 'to sort by')

    # validate select fields.
    if kw['fields']:
        validate_fields(Thing, kw['fields'], 'to select by')

    validate_tag_categories(kw['include_categories'])
    validate_tag_categories(kw['exclude_categories'])
    validate_tag_levels(kw['include_levels'])
    validate_tag_levels(kw['exclude_levels'])
    validate_thing_types(kw['type'])
    validate_event_facets(kw['facets'])

    # base query
    thing_query = Thing.query

    # apply filters
    thing_query, all_event_ids = \
        apply_thing_filters(thing_query, **kw)

    # select event fields
    if kw['fields']:
        columns = [eval('Thing.{}'.format(f)) for f in kw['fields']]
        thing_query = thing_query.with_entities(*columns)

    # apply sort if we havent already sorted by query relevance.
    if kw['sort_field'] != 'relevance':
        sort_obj = eval('Thing.{sort_field}.{direction}'.format(**kw))
        thing_query = thing_query.order_by(sort_obj())

    # facets
    if kw['facets']:

        # TODO
        facets = {}

        # get all thing ids / recipe ids for computing counts
        filter_entities = thing_query.with_entities(Thing.id).all()
        thing_ids = [f[0] for f in filter_entities]

        # if we havent yet retrieved a list of event ids
        if not len(all_event_ids):
            all_event_ids = db.session.query(things_events.c.event_id)\
                .filter(things_events.c.thing_id.in_(thing_ids))\
                .group_by(things_events.c.event_id)\
                .all()
            all_event_ids = [e[0] for e in all_event_ids]

        # number of events associated with these things.
        facets['events'] = len(all_event_ids)

        # excecute count queries
        # TODO: INTEGRATE WITH CELERY
        # thing by type

        if 'types' in kw['facets'] or 'all' in kw['facets']:
            type_counts = db.session\
                .query(Thing.type, func.count(Thing.type))\
                .filter(Thing.id.in_(thing_ids))\
                .group_by(Thing.type)\
                .order_by(desc(func.count(Thing.type)))\
                .all()
            facets['types'] = [dict(zip(['type', 'count'], r))
                               for r in type_counts]

        if 'domains' in kw['facets'] or 'all' in kw['facets']:
            type_counts = db.session\
                .query(Thing.domain, func.count(Thing.domain))\
                .filter(Thing.id.in_(thing_ids))\
                .group_by(Thing.domain)\
                .order_by(desc(func.count(Thing.domain)))\
                .all()
            facets['domains'] = [dict(zip(['domain', 'count'], r))
                                 for r in type_counts]

        # things by recipes
        if 'recipes' in kw['facets'] or 'all' in kw['facets']:
            recipe_counts = db.session\
                .query(Recipe.id, Recipe.name, func.count(Recipe.id))\
                .join(Thing)\
                .filter(Thing.id.in_(thing_ids))\
                .order_by(desc(func.count(Recipe.id)))\
                .group_by(Recipe.id, Recipe.name).all()
            facets['recipes'] = [dict(zip(['id', 'name', 'count'], r))
                                 for r in recipe_counts]

        # things by tag
        if 'tags' in kw['facets'] or 'all' in kw['facets']:
            tag_counts = db.session\
                .query(Tag.id, Tag.name, Tag.type, Tag.level, Tag.category, Tag.color, func.count(Tag.id))\
                .outerjoin(things_tags)\
                .filter(things_tags.c.thing_id.in_(thing_ids))\
                .filter(Tag.type == 'subject')\
                .group_by(Tag.id, Tag.name, Tag.type, Tag.level, Tag.category, Tag.color)\
                .order_by(desc(func.count(Tag.id)))\
                .all()
            facets['tags'] = [dict(zip(['id', 'name', 'type', 'level', 'category', 'color', 'count'], c))
                              for c in tag_counts]

        # events by tag category
        if 'categories' in kw['facets'] or 'all' in kw['facets']:
            category_counts = db.session\
                .query(Tag.category, func.count(Tag.category))\
                .outerjoin(events_tags)\
                .filter(events_tags.c.event_id.in_(all_event_ids))\
                .group_by(Tag.category).all()
            facets['categories'] = [dict(zip(['category', 'count'], c))
                                    for c in category_counts]

        # events by level
        if 'levels' in kw['facets'] or 'all' in kw['facets']:
            level_counts = db.session\
                .query(Tag.level, func.count(Tag.level))\
                .outerjoin(events_tags)\
                .filter(events_tags.c.event_id.in_(all_event_ids))\
                .group_by(Tag.level).all()
            facets['levels'] = [dict(zip(['level', 'count'], c))
                                for c in level_counts]

        # things by task
        if 'tasks' in kw['facets'] or 'all' in kw['facets']:
            task_counts = db.session\
                .query(Task.name, func.count(Task.name))\
                .outerjoin(Recipe)\
                .outerjoin(Thing)\
                .filter(Thing.id.in_(thing_ids))\
                .order_by(desc(func.count(Task.name)))\
                .group_by(Task.name).all()
            facets['tasks'] = [dict(zip(['name', 'count'], c))
                               for c in task_counts]

    # paginate thing_query
    things = thing_query\
        .paginate(kw['page'], kw['per_page'], False)

    # total results
    total = things.total

    # generate pagination urls
    pagination = \
        urls_for_pagination('things.search_things', total, **raw_kw)

    # reformat entites as dictionary
    if kw['fields']:
        things = [dict(zip(kw['fields'], r)) for r in things.items]
    else:
        things = things.items

    resp = {
        'results': things,
        'pagination': pagination,
        'total': total
    }

    if len(kw['facets']):
        resp['facets'] = facets

    return jsonify(resp)


@bp.route('/api/v1/things/<int:thing_id>', methods=['GET'])
@load_user
@load_org
def thing(user, org, thing_id):
    """
    Fetch an individual event.
    """
    t = thing.query.filter_by(id=thing_id, organization_id=org.id).first()
    if not t:
        raise RequestError(
            'An Thing with ID {} does not exist.'.format(event_id))
    return jsonify(t)


# @bp.route('/api/v1/things/<int:thing_id>', methods=['PUT', 'PATCH'])
# @load_user
# @load_org
# def thing_update(user, org, thing_id):
#     """
#     Modify an individual thing.
#     """
#     e = thing.query.filter_by(id=thing_id, organization_id=org.id).first()
#     if not e:
#         raise RequestError(
#             'An thing with ID {} does not exist.'.format(thing_id))

# get request data
#     req_data = request_data()

# fetch tag and thing
#     tag_ids = listify_data_arg('tag_ids')
#     thing_ids = listify_data_arg('thing_ids')

# check for current status / PUT status
#     current_status = e.status
#     req_status = req_data.get('status')

#     if len(tag_ids) and len(thing_ids):

#         approve = True
#         tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
#         if not len(tags):
#             raise RequestError(
#                 'Tag(s) with ID(s) {} do(es) not exist.'.format(tag_ids))

#         things = Thing.query.filter(Thing.id.in_(thing_ids)).all()
#         if not len(things):
#             raise RequestError(
#                 'Thing(s) with ID(s) {} do(es) not exist.'.format(tag_ids))

# check for incomplete approval requests.
#     elif current_status != 'approved' and req_status == 'approved':

#         raise RequestError(
#             'To approve an thing you must assign it to one or more '
#             'Things or Tags by using the "thing_ids" and "tag_ids" fields.')

#     else:
#         approve = False

# filter out any non-columns
#     columns = get_table_columns(thing)
#     for k in req_data.keys():
#         if k not in columns:
#             req_data.pop(k)

# if we're approving this thing, override status
#     if approve:
#         req_data['status'] = 'approved'

# add "updated" dat
#     req_data['updated'] = dates.now()

# update fields
#     for k, v in req_data.items():
#         setattr(e, k, v)

# ensure no one sneakily/accidentally
# updates an organization id
#     e.organization_id = org.id

# if we're approving, add tags + things
#     if approve:

# only add things + tags that haven't already been assigned.
#         for thing, tag in zip(things, tags):
#             if thing.id not in e.thing_ids:
#                 e.things.append(thing)

# validate tag
#             if tag.type != 'impact':
#                 raise RequestError('things can only be assigned Impact Tags.')

# add it
#             if tag.id not in e.tag_ids:
#                 e.tags.append(tag)

# commit changes
#     db.session.add(e)
#     db.session.commit()

# return modified thing
#     return jsonify(e)


# @bp.route('/api/v1/things/<int:thing_id>', methods=['DELETE'])
# @load_user
# @load_org
# def thing_delete(user, org, thing_id):
#     """
#     Delete an individual thing. Here, we do not explicitly "delete"
#     the thing, but update it's status instead. This will help
#     when polling recipes for new things since we'll be able to ensure
#     that we do not create duplicate things.
#     """
#     e = thing.query.filter_by(id=thing_id, organization_id=org.id).first()
#     if not e:
#         raise RequestError(
#             'An thing with ID {} does not exist.'.format(thing_id))

# remove associations
# from
# http://stackoverflow.com/questions/9882358/how-to-delete-rows-from-a-table-using-an-sqlalchemy-query-without-orm
#     d = things_tags.delete(things_tags.c.thing_id == thing_id)
#     db.session.execute(d)

#     d = things_things.delete(things_things.c.thing_id == thing_id)
#     db.session.execute(d)

# update thing
#     e.status = 'deleted'
#     e.updated = dates.now()

# add object
#     db.session.add(e)
#     db.session.commit()

# return modified event
#     return jsonify(e)


# @bp.route('/api/v1/events/<int:event_id>/tags/<int:tag_id>', methods=['PUT', 'PATCH'])
# @load_user
# @load_org
# def event_add_tag(user, org, event_id, tag_id):
#     """
#     Add a tag to an event.
#     """
#     e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
#     if not e:
#         raise RequestError(
#             'An Event with ID {} does not exist.'.format(event_id))

#     if not e.status == 'approved':
#         raise RequestError(
#             'You must first approve an Event before adding additional Tags.')

#     tag = Tag.query.filter_by(id=tag_id, organization_id=org.id).first()
#     if not tag:
#         raise RequestError(
#             'Tag with ID {} does not exist.'.format(tag_id))

#     print(tag.to_dict())
#     if tag.type != 'impact':
#         raise RequestError('Events can only be assigned Impact Tags.')

#     if tag.id not in e.tag_ids:
#         e.tags.append(tag)

#     e.updated = dates.now()
#     db.session.add(e)
#     db.session.commit()

# return modified event
#     return jsonify(e)


# @bp.route('/api/v1/events/<int:event_id>/tags/<int:tag_id>', methods=['DELETE'])
# @load_user
# @load_org
# def event_delete_tag(user, org, event_id, tag_id):
#     """
#     Add a tag to an event.
#     """
#     e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
#     if not e:
#         raise RequestError(
#             'An Event with ID {} does not exist.'.format(event_id))

#     if tag_id not in e.tag_ids:
#         raise RequestError(
#             'An Event with ID {} does not currently have an association '
#             'with a Tag with ID {}'.format(event_id, tag_id))

#     for tag in e.tags:
#         if tag.id == tag_id:
#             e.tags.remove(tag)

#     e.updated = dates.now()
#     db.session.add(e)
#     db.session.commit()

# return modified event
#     return jsonify(e)


# @bp.route('/api/v1/events/<int:event_id>/things/<int:thing_id>', methods=['PUT'])
# @load_user
# @load_org
# def event_add_thing(user, org, event_id, thing_id):
#     """
#     Add a tag to an event.
#     """
#     e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
#     if not e:
#         raise RequestError(
#             'An Event with ID {} does not exist.'.format(event_id))

#     if not e.status == 'approved':
#         raise RequestError(
#             'You must first approve an Event before adding additional Things.')

#     thing = Thing.query.filter_by(id=thing_id, organization_id=org.id).first()
#     if not thing:
#         raise RequestError(
#             'Thing with ID {} does not exist.'.format(thing_id))

#     if thing.id not in e.thing_ids:
#         e.things.append(thing)

#     e.updated = dates.now()
#     db.session.add(e)
#     db.session.commit()

# return modified event
#     return jsonify(e)


# @bp.route('/api/v1/events/<int:event_id>/things/<int:thing_id>', methods=['DELETE'])
# @load_user
# @load_org
# def event_delete_thing(user, org, event_id, thing_id):
#     """
#     Add a tag to an event.
#     """
#     e = Event.query.filter_by(id=event_id, organization_id=org.id).first()
#     if not e:
#         raise RequestError(
#             'An Event with ID {} does not exist.'.format(event_id))

#     if thing_id not in e.thing_ids:
#         raise RequestError(
#             'An Event with ID {} does not currently have an association '
#             'with a Thing with ID {}'.format(event_id, thing_id))

#     for thing in e.things:
#         if thing.id == thing_id:
#             e.things.remove(thing)

#     e.updated = dates.now()
#     db.session.add(e)
#     db.session.commit()

# return modified event
#     return jsonify(e)
