from collections import defaultdict, Counter

from sqlalchemy import func
from flask import Blueprint

from newslynx.core import db
from newslynx.exc import RequestError
from newslynx.models import Tag
from newslynx.models.relations import events_tags, things_tags
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.models.util import get_table_columns
from newslynx.views.util import *
from newslynx.taxonomy import (
    IMPACT_TAG_CATEGORIES, IMPACT_TAG_LEVELS)

# blueprint
bp = Blueprint('tags', __name__)


@bp.route('/api/v1/tags', methods=['GET'])
@load_user
@load_org
def get_tags(user, org):
    """
    Get all tags + counts for an organization.
    """
    # base query

    # TODO: count number of things that have been assigned events with tags?
    tag_query = db.session\
        .query(Tag.id, Tag.organization_id, Tag.name, Tag.type,
               Tag.level, Tag.category, Tag.color,
               func.count(events_tags.c.event_id), func.count(things_tags.c.thing_id))\
        .outerjoin(events_tags)\
        .outerjoin(things_tags)\
        .filter(Tag.organization_id == org.id)\
        .group_by(Tag.id)

    # optionall filter by type/level/category
    type = arg_str('type', default=None)
    level = arg_str('level', default=None)
    category = arg_str('category', default=None)

    if type:
        validate_tag_types(type)
        tag_query = tag_query.filter(Tag.type == type)

    if level:
        validate_tag_levels(level)
        tag_query = tag_query.filter(Tag.level == level)

    if category:
        validate_tag_categories(category)
        tag_query = tag_query.filter(Tag.category == category)

    tag_cols = ['id', 'organization_id', 'name', 'type', 'level',
                'category', 'color', 'event_count', 'thing_count']
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
            t.pop('thing_count')
        else:
            t.pop('event_count')
            t.pop('level')
            t.pop('category')
        clean_tags.append(t)

    # format response
    resp = {'tags': clean_tags, 'facets': c}

    return jsonify(resp)


@bp.route('/api/v1/tags/categories', methods=['GET'])
def tag_categores():
    """
    A helper for generating dynamic UIs
    """
    return jsonify({'categories': IMPACT_TAG_CATEGORIES})


@bp.route('/api/v1/tags/levels', methods=['GET'])
def tag_levels():
    """
    A helper for generating dynamic UIs
    """
    return jsonify({'levels': IMPACT_TAG_LEVELS})


@bp.route('/api/v1/tags', methods=['POST'])
@load_user
@load_org
def create_tag(user, org):
    """
    Get all tags for an organization.
    """

    req_data = request_data()

    # check for required keys
    for k in ['name', 'type', 'color']:
        if k not in req_data:
            raise RequestError('A Tag requires a "name", "color", and "type"')

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

        validate_tag_categories(tag['category'])
        validate_tag_levels(tag['level'])

    # create the tag
    tag = Tag(organization_id=org.id, **req_data)

    db.session.add(tag)

    # check for dupes
    try:
        db.session.commit()
    except Exception as err:
        raise RequestError(err.message)

    return jsonify(tag)


@bp.route('/api/v1/tags/<tag_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_tag(user, org, tag_id):
    """
    Update an individual tag.
    """
    # fetch the tag object
    tag = Tag.query.filter_by(organization_id=org.id, id=tag_id).first()
    if not tag:
        raise RequestError('A Tag with ID {} does not exist'.format(tag_id))

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
            validate_tag_categories(tag['category'])
            validate_tag_levels(tag['level'])

    # check if levels + categories are being assigned to
    # subject tags
    if tag.type == 'subject':
        if req_data.get('category') or req_data.get('level'):
            raise RequestError(
                'Categories and Levels can only be set for Impact Tags')

    # set organization id
    req_data['organization_id'] = org.id

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
    tag = Tag.query.filter_by(organization_id=org.id, id=tag_id).first()
    if not tag:
        raise RequestError('A Tag with ID {} does not exist'.format(tag_id))

    db.session.delete(tag)
    db.session.commit()
    return delete_response()
