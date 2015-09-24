from collections import defaultdict, Counter

from sqlalchemy import func, update
from flask import Blueprint

from newslynx.core import db
from newslynx.models import Tag
from newslynx.models.relations import events_tags, content_items_tags
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.models.util import get_table_columns
from newslynx.tasks import rollup_metric
from newslynx.views.util import *
from newslynx.constants import (
    IMPACT_TAG_CATEGORIES, IMPACT_TAG_LEVELS)
from newslynx.exc import (
    RequestError, NotFoundError, ConflictError)

# blueprint
bp = Blueprint('tags', __name__)


@bp.route('/api/v1/tags', methods=['GET'])
@load_user
@load_org
def get_tags(user, org):
    """
    Get all tags + counts for an org.
    """
    # base query

    # TODO: count number of things that have been assigned events with tags?
    tag_query = db.session\
        .query(Tag.id, Tag.org_id, Tag.name, Tag.slug, Tag.type,
               Tag.level, Tag.category, Tag.color, Tag.created, Tag.updated,
               func.count(events_tags.c.event_id),
               func.count(content_items_tags.c.content_item_id))\
        .outerjoin(events_tags)\
        .outerjoin(content_items_tags)\
        .filter(Tag.org_id == org.id)\
        .group_by(Tag.id)

    # optionally filter by type/level/category
    type = arg_str('type', default=None)
    level = arg_str('level', default=None)
    category = arg_str('category', default=None)

    sort_field, direction = \
        arg_sort('sort', default='created')

    # filters
    if type:
        validate_tag_types(type)
        tag_query = tag_query.filter(Tag.type == type)

    if level:
        validate_tag_levels(level)
        tag_query = tag_query.filter(Tag.level == level)

    if category:
        validate_tag_categories(category)
        tag_query = tag_query.filter(Tag.category == category)

    # sort
    validate_fields(Tag, fields=[sort_field], suffix='to sort by')
    sort_obj = eval('Tag.{}.{}'.format(sort_field, direction))
    tag_query = tag_query.order_by(sort_obj())

    tag_cols = ['id', 'org_id', 'name', 'slug', 'type', 'level',
                'category', 'color', 'created', 'updated',
                'event_count', 'content_item_count']

    tags = [dict(zip(tag_cols, r)) for r in tag_query.all()]

    # just compute facets via python rather
    # than hitting the database.
    clean_tags = []
    c = defaultdict(Counter)
    for t in tags:
        c['types'][t['type']] += 1
        if t['level']:
            c['levels'][t['level']] += 1
        if t['category']:
            c['categories'][t['category']] += 1

        # TODO: refine query so we don't need to do this.
        if t['type'] == 'impact':
            t.pop('content_item_count', None)
        else:
            t.pop('event_count')
            t.pop('level')
            t.pop('category')
        clean_tags.append(t)

    # format response
    return jsonify({'tags': clean_tags, 'facets': c})


@bp.route('/api/v1/tags', methods=['POST'])
@load_user
@load_org
def create_tag(user, org):
    """
    Create a tag.
    """

    req_data = request_data()

    # check for required keys
    for k in ['name', 'type', 'color']:
        if k not in req_data:
            raise RequestError(
                'A Tag requires a "name", "color", and "type"')

    # check hex code
    validate_hex_code(req_data['color'])

    # check tag type
    validate_tag_types(req_data['type'])

    # if tag type is "impact" ensure a proper category and level are included
    if req_data['type'] == 'impact':
        for k in ['level', 'category']:
            if k not in req_data:
                raise RequestError(
                    'An Impact Tag requires a "level" and "category"')

        validate_tag_categories(req_data['category'])
        validate_tag_levels(req_data['level'])

    elif req_data['type'] == 'subject':
        for k in ['level', 'category']:
            if k in req_data:
                raise RequestError(
                    'Categories and Levels can only be set for Impact Tags.')

    # create the tag
    tag = Tag(org_id=org.id, **req_data)

    db.session.add(tag)

    # check for dupes
    try:
        db.session.commit()
    except Exception as err:
        raise ConflictError(err.message)

    return jsonify(tag)


@bp.route('/api/v1/tags/<tag_id>', methods=['GET'])
@load_user
@load_org
def get_tag(user, org, tag_id):
    """
    GET an individual tag.
    """
    # fetch the tag object
    tag = fetch_by_id_or_field(Tag, 'slug', tag_id, org_id=org.id)
    if not tag:
        raise NotFoundError(
            'A Tag with ID {} does not exist'
            .format(tag_id))

    return jsonify(tag)


@bp.route('/api/v1/tags/<tag_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_tag(user, org, tag_id):
    """
    Update an individual tag.
    """
    # fetch the tag object
    tag = fetch_by_id_or_field(Tag, 'slug', tag_id, org_id=org.id)
    if not tag:
        raise NotFoundError(
            'A Tag with ID {} does not exist'
            .format(tag_id))

    # fetch the request data.
    req_data = request_data()

    # check hex code
    if 'color' in req_data:
        validate_hex_code(req_data['color'])

    # check tag type
    if 'type' in req_data:
        validate_tag_types(req_data['type'])

        # if tag type is "impact" ensure a proper category and
        # level are included
        if req_data['type'] == 'impact':
            validate_tag_categories(req_data['category'])
            validate_tag_levels(req_data['level'])

    # check if levels + categories are being assigned to
    # subject tags
    if tag.type == 'subject':
        if req_data.get('category') or req_data.get('level'):
            raise RequestError(
                'Categories and Levels can only be set for Impact Tags')

    # set org id
    req_data['org_id'] = org.id

    # filter out non-table columns
    columns = get_table_columns(Tag)
    for k in req_data.keys():
        if k not in columns:
            req_data.pop(k)

    # update attributes
    for k, v in req_data.items():
        setattr(tag, k, v)

    db.session.add(tag)

    # check for dupes
    try:
        db.session.commit()
    except Exception as err:
        raise RequestError(err.message)

    return jsonify(tag)


@bp.route('/api/v1/tags/<tag_id>', methods=['DELETE'])
@load_user
@load_org
def delete_tag(user, org, tag_id):
    """
    Delete an individual tag.
    """
    # fetch the tag object
    tag = fetch_by_id_or_field(Tag, 'slug', tag_id, org_id=org.id)
    if not tag:
        raise NotFoundError(
            'A Tag with ID {} does not exist'
            .format(tag_id))

    db.session.delete(tag)
    db.session.commit()
    return delete_response()


@bp.route('/api/v1/tags/<int:from_tag_id>/merge/<int:to_tag_id>', methods=['PUT'])
@load_user
@load_org
def merge_tags(user, org, from_tag_id, to_tag_id):
    """
    Merge two tags of the same type and all their associations.
    from_tag_id is deleted and it's associations are merged into to_tag_id
    """
    from_t = Tag.query\
        .filter_by(id=from_tag_id, org_id=org.id)\
        .first()

    if not from_t:
        raise NotFoundError(
            'Tag with ID "{}" does not exist."'
            .format(from_tag_id))

    to_t = Tag.query\
        .filter_by(id=to_tag_id, org_id=org.id)\
        .first()

    if not to_t:
        raise NotFoundError(
            'Tag with ID "{}" does not exist."'
            .format(to_tag_id))

    if not from_t.type == to_t.type:
        raise RequestError('You can only merge tags of the same type.')

    if from_t.type == 'subject':

        # re associate content
        stmt = update(content_items_tags)\
            .where(content_items_tags.c.tag_id == from_tag_id)\
            .values(tag_id=to_tag_id)
        db.session.execute(stmt)

        # remove from tag
        db.session.delete(from_t)
        db.session.commit()

    if from_t.type == 'impact':
        # re associate events
        stmt = update(events_tags)\
            .where(events_tags.c.tag_id == from_tag_id)\
            .values(tag_id=to_tag_id)
        db.session.execute(stmt)

        # get all associated content item IDS.
        content_item_ids = [
            c.id for e in from_t.events for c in e.content_item_ids]
        content_item_ids.append(
            [c.id for e in to_t.events for c in e.content_item_ids])

        # remove from tag
        db.session.delete(from_t)
        db.session.commit()

        # update event metrics
        if len(content_item_ids):
            # update event-level metrics for this content item id
            rollup_metric.content_summary_from_events(org, content_item_ids)

    return jsonify(to_t)


@bp.route('/api/v1/tags/categories', methods=['GET'])
def tag_categores():
    """
    A helper for generating dynamic UIs
    """
    return jsonify(IMPACT_TAG_CATEGORIES)


@bp.route('/api/v1/tags/levels', methods=['GET'])
def tag_levels():
    """
    A helper for generating dynamic UIs
    """
    return jsonify(IMPACT_TAG_LEVELS)
