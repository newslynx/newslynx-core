from gevent.pool import Pool

from copy import copy

from flask import Blueprint
from sqlalchemy.dialects import postgresql

from sqlalchemy import distinct
from sqlalchemy.types import Numeric
from newslynx.core import db
from newslynx.exc import NotFoundError
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.tasks import load as load_data
from newslynx.tasks import facet
from newslynx.models.relations import content_items_events, events_tags
from newslynx.views.util import *
from newslynx.models import (
    ContentItem, Author, ContentMetricSummary, Tag, Event)
from newslynx.constants import (
    CONTENT_ITEM_FACETS, CONTENT_ITEM_EVENT_FACETS)

# blueprint
bp = Blueprint('content', __name__)


# utils
content_facet_pool = Pool(len(CONTENT_ITEM_FACETS))


# TODO: Generalize this with `apply_event_filters`
def apply_content_item_filters(q, **kw):
    """
    Given a base ContentItem.query, apply all filters.
    """

    # filter by org_id
    q = q.filter(ContentItem.org_id == kw['org_id'])

    # use this for keeping track of
    # levels/categories events.
    all_event_ids = set()

    # apply search query
    if kw['search_query']:
        if kw['sort_field'] == 'relevance':
            sort = True
        else:
            sort = False
        if kw['search_vector'] == 'all':
            vector = ContentItem.title_search_vector | \
                ContentItem.description_search_vector | \
                ContentItem.body_search_vector | \
                Author.search_vector | \
                ContentItem.meta_search_vector

        elif kw['search_vector'] == 'authors':
            vector = Author.search_vector

        else:
            vname = "{}_search_vector".format(kw['search_vector'])
            vector = getattr(ContentItem, vname)

        q = q.search(kw['search_query'], vector=vector, sort=sort)

    # apply status filter
    if kw['type'] != 'all':
        q = q.filter(ContentItem.type == kw['type'])

    if kw['provenance']:
        q = q.filter(ContentItem.provenance == kw['provenance'])

    # filter url by regex
    if kw['url']:
        q = q.filter_by(url=kw['url'])

    # filter url by regex
    if kw['url_regex']:
        q = q.filter(text('content.url ~ :regex')).params(
            regex=kw['url_regex'])

    # filter by domain
    if kw['domain']:
        q = q.filter(ContentItem.domain == kw['domain'])

    # apply date filters
    if kw['created_after']:
        q = q.filter(ContentItem.created >= kw['created_after'])

    if kw['created_before']:
        q = q.filter(ContentItem.created <= kw['created_before'])

    if kw['updated_after']:
        q = q.filter(ContentItem.updated >= kw['updated_after'])

    if kw['updated_before']:
        q = q.filter(ContentItem.updated <= kw['updated_before'])

    # apply recipe filter
    if len(kw['include_recipes']):
        q = q.filter(ContentItem.recipe_id.in_(kw['include_recipes']))

    if len(kw['exclude_recipes']):
        q = q.filter(~ContentItem.recipe_id.in_(kw['exclude_recipes']))

    # apply tag categories/levels filter
    # TODO try not to use multiple queries here.
    if len(kw['include_categories']):

        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(org_id=kw['org_id'])\
            .filter(Tag.category.in_(kw['include_categories']))\
            .all()

        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            all_event_ids.add(e)

        q = q.filter(ContentItem.events.any(
            Event.id.in_(event_ids)))

    if len(kw['exclude_categories']):

        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(org_id=kw['org_id'])\
            .filter(Tag.category.in_(kw['exclude_categories']))\
            .all()
        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            if e in all_event_ids:
                all_event_ids.remove(e)
        q = q.filter(~ContentItem.events.any(Event.id.in_(event_ids)))

    if len(kw['include_levels']):

        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(org_id=kw['org_id'])\
            .filter(Tag.level.in_(kw['include_levels']))\
            .all()
        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            all_event_ids.add(e)
        q = q.filter(ContentItem.events.any(
            Event.id.in_(event_ids)))

    if len(kw['exclude_levels']):
        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(org_id=kw['org_id'])\
            .filter(Tag.level.in_(kw['exclude_levels']))\
            .all()

        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            if e in all_event_ids:
                all_event_ids.remove(e)

        q = q.filter(~ContentItem.events.any(
            Event.id.in_(event_ids)))

    if len(kw['include_impact_tags']):

        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(org_id=kw['org_id'])\
            .filter(Tag.id.in_(kw['include_impact_tags']))\
            .all()
        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            all_event_ids.add(e)
        q = q.filter(ContentItem.events.any(
            Event.id.in_(event_ids)))

    if len(kw['exclude_impact_tags']):
        event_ids = db.session.query(events_tags.c.event_id)\
            .join(Tag)\
            .filter_by(org_id=kw['org_id'])\
            .filter(Tag.id.in_(kw['exclude_impact_tags']))\
            .all()

        event_ids = [e[0] for e in event_ids]
        for e in event_ids:
            if e in all_event_ids:
                all_event_ids.remove(e)
        q = q.filter(~ContentItem.events.any(
            Event.id.in_(event_ids)))

    # apply tags filter
    if len(kw['include_subject_tags']):
        q = q.filter(ContentItem.tags.any(
            Tag.id.in_(kw['include_subject_tags'])))

    if len(kw['exclude_subject_tags']):
        q = q.filter(~ContentItem.tags.any(
            Tag.id.in_(kw['exclude_subject_tags'])))

    # apply authors filter
    if len(kw['include_authors']):
        q = q.filter(ContentItem.authors.any(
            Author.id.in_(kw['include_authors'])))

    if len(kw['exclude_authors']):
        q = q.filter(~ContentItem.authors.any(
            Author.id.in_(kw['exclude_authors'])))

    # apply sous_chefs filter
    # TODO: DONT USE MULTIPLE QUERIES HERE
    if len(kw['include_sous_chefs']):
        sous_chef_recipes = db.session.query(Recipe.id)\
            .filter(Recipe.sous_chef.has(
                SousChef.slug.in_(kw['include_sous_chefs'])))\
            .all()
        recipe_ids = [r[0] for r in sous_chef_recipes]
        q = q.filter(ContentItem.recipe_id.in_(recipe_ids))

    if len(kw['exclude_sous_chefs']):
        sous_chef_recipes = db.session.query(Recipe.id)\
            .filter(Recipe.sous_chef.has(
                SousChef.slug.in_(kw['exclude_sous_chefs'])))\
            .all()
        recipe_ids = [r[0] for r in sous_chef_recipes]
        q = q.filter(~ContentItem.recipe_id.in_(recipe_ids))

    # apply ids filter.
    if len(kw['include_content_items']):
        q = q.filter(ContentItem.id.in_(kw['include_content_items']))

    if len(kw['exclude_content_items']):
        q = q.filter(~ContentItem.id.in_(kw['exclude_content_items']))

    return q, list(all_event_ids)


# endpoints

@bp.route('/api/v1/content', methods=['GET'])
@load_user
@load_org
def search_content(user, org):
    """
    args:
        q                | search query
        url              | a regex for a url
        domain           | a domain to match on
        fields           | a comma-separated list of fields to include in response
        page             | page number
        per_page         | number of items per page.
        sort             | variable to order by, preface with '-' to sort desc.
        created_after    | isodate variable to filter results after
        created_before   | isodate variable to filter results before
        updated_after    | isodate variable to filter results after
        updated_before   | isodate variable to filter results before
        type             | ['pending', 'approved', 'deleted']
        facets           | a comma-separated list of facets to include, default=[]
        tag              | a comma-separated list of tags to filter by
        categories       | a comma-separated list of tag_categories to filter by
        levels           | a comma-separated list of tag_levels to filter by
        content_item_ids | a comma-separated list of content_item_ids to filter by.
        subject_tag_ids  | a comma-separated list of subject_tag_ids to filter by
        impact_tag_ids   | a comma-separated list of impact_tag_ids to filter by
        recipe_ids       | a comma-separated list of recipes to filter by
        sous_chefs       | a comma-separated list of sous_chefs to filter by
        url_regex        | what does it sound like
        url              | duh
    """

    # parse arguments

    # store raw kwargs for generating pagination urls..
    raw_kw = dict(request.args.items())
    raw_kw['apikey'] = user.apikey
    raw_kw['org'] = org.id

    # special arg tuples
    sort_field, direction = \
        arg_sort('sort', default='-created')
    include_subject_tags, exclude_subject_tags = \
        arg_list('subject_tag_ids', default=[], typ=int, exclusions=True)
    include_impact_tags, exclude_impact_tags = \
        arg_list('impact_tag_ids', default=[], typ=int, exclusions=True)
    include_recipes, exclude_recipes = \
        arg_list('recipe_ids', default=[], typ=int, exclusions=True)
    include_content_items, exclude_content_items = \
        arg_list('ids', default=[], typ=int, exclusions=True)
    include_sous_chefs, exclude_sous_chefs = \
        arg_list('sous_chefs', default=[], typ=str, exclusions=True)
    include_authors, exclude_authors = \
        arg_list('author_ids', default=[], typ=int, exclusions=True)
    include_levels, exclude_levels = \
        arg_list('levels', default=[], typ=str, exclusions=True)
    include_categories, exclude_categories = \
        arg_list('categories', default=[], typ=str, exclusions=True)

    kw = dict(
        search_query=arg_str('q', default=None),
        search_vector=arg_str('search', default='all'),
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
        provenance=arg_str('provenance', default=None),
        incl_body=arg_bool('incl_body', default=False),
        incl_img=arg_bool('incl_img', default=False),
        incl_metrics=arg_bool('incl_metrics', default=True),
        facets=arg_list('facets', default=[], typ=str),
        include_categories=include_categories,
        exclude_categories=exclude_categories,
        include_levels=include_levels,
        exclude_levels=exclude_levels,
        include_subject_tags=include_subject_tags,
        exclude_subject_tags=exclude_subject_tags,
        include_impact_tags=include_impact_tags,
        exclude_impact_tags=exclude_impact_tags,
        include_authors=include_authors,
        exclude_authors=exclude_authors,
        include_recipes=include_recipes,
        exclude_recipes=exclude_recipes,
        include_sous_chefs=include_sous_chefs,
        exclude_sous_chefs=exclude_sous_chefs,
        include_content_items=include_content_items,
        exclude_content_items=exclude_content_items,
        sort_ids=arg_bool('sort_ids', default=False),
        url=arg_str('url', default=None),
        url_regex=arg_str('url_regex', default=None),
        org_id=org.id
    )

    # validate arguments

    # validate sort fields are part of Event object.
    if kw['sort_field'] and \
       kw['sort_field'] != 'relevance' and not \
       kw['sort_field'].startswith('metrics'):

        metric_sort = False
        try:
            validate_fields(
                ContentItem, fields=[kw['sort_field']], suffix='to sort by')

        except Exception as e:
            raise RequestError("{} To sort by a metric, you must use the following "
                               "format: 'metrics.<metric_name>'."
                               .format(e.message))

    # validate metric sort fields
    elif kw['sort_field'].startswith('metrics'):

        metric_sort = True

        parts = kw['sort_field'].split('.')
        if len(parts) != 2:
            raise RequestError(
                "To sort by a metric, you must use the following "
                "format: 'metrics.<metric_name>'. You input '{}'."
                .format(kw['sort_field']))

        # fetch metrics
        metrics_names = org.content_summary_metric_names

        # make sure this is a valid metric to sort by.
        metric_name = parts[-1]

        if metric_name not in metrics_names:
            raise RequestError(
                "'{}' is not a valid metric to sort by. "
                "Choose from: {}"
                .format(metric_name, metrics_names))

        kw['sort_field'] = metric_name

    # validate select fields.
    if kw['fields']:
        validate_fields(
            ContentItem, fields=kw['fields'], suffix='to select by')

    validate_tag_categories(kw['include_categories'])
    validate_tag_categories(kw['exclude_categories'])
    validate_tag_levels(kw['include_levels'])
    validate_tag_levels(kw['exclude_levels'])
    validate_content_item_types(kw['type'])
    validate_content_item_provenances(kw['provenance'])
    validate_content_item_search_vector(kw['search_vector'])

    # base query
    content_query = ContentItem.query

    # apply filters
    content_query, event_ids = \
        apply_content_item_filters(content_query, **kw)

    # select event fields
    if kw['fields']:
        cols = [eval('ContentItem.{}'.format(f)) for f in kw['fields']]
        content_query = content_query.with_entities(*cols)

    # apply sort if we havent already sorted by query relevance.
    paginate = True
    if not kw['sort_ids']:
        if kw['sort_field'] != 'relevance':
            if not metric_sort:
                p = "ContentItem.{sort_field}.{direction}"
            else:
                p = "ContentMetricSummary.metrics['{sort_field}'].cast(Numeric).{direction}"

            content_query = content_query\
                .order_by(eval(p.format(**kw))().nullslast())

    elif len(include_content_items):
        ids = [str(i) for i in include_content_items]
        if len(ids) > 100:
            raise RequestError('You cannot include an array of content item ids longer than 100 elements.')
        sort_str = "content_idx(ARRAY[{}], content.id)".format(",".join(ids))
        content_query = content_query.order_by(sort_str)
        paginate = False

    # facets
    validate_content_item_facets(kw['facets'])
    if kw['facets']:

        # set all facets
        if 'all' in kw['facets']:
            kw['facets'] = copy(CONTENT_ITEM_FACETS)

        # get all content_items ids for computing counts
        content_item_ids = content_query\
            .with_entities(ContentItem.id)\
            .all()
        content_item_ids = [t[0] for t in content_item_ids]

        # if we havent yet retrieved a list of event ids,
        # fetch this list only if the facets that require them
        # are included in the request
        if not len(event_ids):
            if any([f in kw['facets'] for f in CONTENT_ITEM_EVENT_FACETS]):
                event_ids = db.session.query(distinct(content_items_events.c.event_id))\
                    .filter(content_items_events.c.content_item_id.in_(content_item_ids))\
                    .group_by(content_items_events.c.event_id)\
                    .all()
                event_ids = [ee[0] for ee in event_ids]

        # pooled faceting function
        def fx(by):
            if by in CONTENT_ITEM_EVENT_FACETS:
                if by == 'event_statuses':
                    return by, facet.events('statuses', event_ids)
                elif by == 'events':
                    return by, len(event_ids)
                return by, facet.events(by, event_ids)
            return by, facet.content_items(by, content_item_ids)

        # dict of results
        facets = {}
        for by, result in content_facet_pool.imap_unordered(fx, kw['facets']):
            facets[by] = result

    if paginate:
        content = content_query\
            .paginate(kw['page'], kw['per_page'], False)
        total = content.total
        content = content.items

    else:
        content = content_query.all()
        total = len(content)

    # generate pagination urls
    pagination = \
        urls_for_pagination('content.search_content', total, **raw_kw)

    print content_query
    # reformat entites as dictionary
    if kw['fields']:
        content = [dict(zip(kw['fields'], r)) for r in content]
    else:
        content = [t.to_dict(**kw) for t in content]

    resp = {
        'content_items': content,
        'pagination': pagination,
        'total': total
    }

    if len(kw['facets']):
        resp['facets'] = facets

    return jsonify(resp)


@bp.route('/api/v1/content', methods=['POST'])
@load_user
@load_org
def create_content(user, org):
    """
    Create a content item
    """
    req_data = request_data()
    extract = arg_bool('extract', default=True)
    recipe_id = arg_str('recipe_id', default=None)

    content = load_data.content(
        req_data,
        org_id=org.id,
        recipe_id=recipe_id,
        extract=extract,
        queued=False)
    if len(content) == 1:
        content = content[0]
    return jsonify(content)


@bp.route('/api/v1/content/bulk', methods=['POST'])
@load_user
@load_org
def bulk_create_content(user, org):
    """
    bulk create content items.
    """
    req_data = request_data()
    extract = arg_bool('extract', default=True)
    recipe_id = arg_str('recipe_id', default=None)

    job_id = load_data.content(
        req_data,
        org_id=org.id,
        recipe_id=recipe_id,
        extract=extract,
        queued=True)
    ret = url_for_job_status(apikey=user.apikey, job_id=job_id, queue='bulk')
    return jsonify(ret)


@bp.route('/api/v1/content/<int:content_item_id>', methods=['GET'])
@load_user
@load_org
def get_content_item(user, org, content_item_id):
    """
    Create a content item
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id, org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'An ContentItem with ID {} does not exist.'
            .format(content_item_id))
    return jsonify(c.to_dict(incl_body=True))


@bp.route('/api/v1/content/<int:content_item_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_content_item(user, org, content_item_id):
    """
    Update an individual content-item.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id, org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'An ContentItem with ID {} does not exist.'
            .format(content_item_id))

    # get request data
    req_data = request_data()

    # fetch tags
    tag_ids = listify_data_arg('tag_ids')

    # check for current status / PUT status
    if len(tag_ids):
        tags = Tag.query\
            .filter_by(org_id=org.id)\
            .filter(Tag.id.in_(tag_ids))\
            .all()

        if not len(tags):
            raise RequestError(
                'Tag(s) with ID(s) {} do(es) not exist.'
                .format(tag_ids))

        for t in tags:
            if t.type != 'subject':
                raise RequestError(
                    'Only subject tags can be applied to Content Items')
            if t.id not in c.tag_ids:
                c.tags.append(t)

    # filter out any non-columns
    columns = get_table_columns(ContentItem)
    for k in req_data.keys():
        if k not in columns or k in ['org_id', 'id']:
            req_data.pop(k)

    # update fields
    for k, v in req_data.items():
        setattr(c, k, v)
    try:
        db.session.add(c)
        db.session.commit()
    
    except Exception as e:
        raise RequestError(
            'There was a problem updating this Content Item. '
            'Here is the error: {}'
            .format(e.message))
    return jsonify(c)


@bp.route('/api/v1/content/<int:content_item_id>', methods=['DELETE'])
@load_user
@load_org
def delete_content_item(user, org, content_item_id):
    """
    Update an individual content-item.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id, org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'An ContentItem with ID {} does not exist.'
            .format(content_item_id))

    # delete metrics
    cmd = """
    DELETE FROM content_metric_timeseries WHERE content_item_id = {0};
    DELETE FROM content_metric_summary WHERE content_item_id = {0};
    """.format(content_item_id)

    # delete content item + metrics
    db.session.execute(cmd)
    db.session.delete(c)
    db.session.commit()

    return delete_response()


@bp.route('/api/v1/content/<int:content_item_id>/tags/<int:tag_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def content_item_add_tag(user, org, content_item_id, tag_id):
    """
    Add a tag to an content_item.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id, org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'An ContentItem with ID {} does not exist.'
            .format(content_item_id))

    tag = Tag.query\
        .filter_by(id=tag_id, org_id=org.id)\
        .first()

    if not tag:
        raise NotFoundError(
            'Tag with ID {} does not exist.'
            .format(tag_id))

    if tag.type != 'subject':
        raise RequestError(
            'Content Items can only be assigned Subject Tags.')

    if tag.id not in c.subject_tag_ids:
        c.tags.append(tag)

    db.session.add(c)
    db.session.commit()

    # return modified content item
    return jsonify(c)


@bp.route('/api/v1/content/<int:content_item_id>/tags/<int:tag_id>',
          methods=['DELETE'])
@load_user
@load_org
def content_item_delete_tag(user, org, content_item_id, tag_id):
    """
    Remove a tag from a content item.
    """
    c = ContentItem.query\
        .filter_by(id=content_item_id, org_id=org.id)\
        .first()

    if not c:
        raise NotFoundError(
            'An ContentItem with ID {} does not exist.'
            .format(content_item_id))

    tag = Tag.query\
        .filter_by(id=tag_id, org_id=org.id)\
        .first()

    if not tag:
        raise NotFoundError(
            'Tag with ID {} does not exist.'
            .format(tag_id))

    for tag in c.tags:
        if tag.id == tag_id:
            c.tags.remove(tag)

    db.session.add(c)
    db.session.commit()

    # return modified content item
    return jsonify(c)
