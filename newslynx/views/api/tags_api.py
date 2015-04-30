from flask import Blueprint

from newslynx.core import db
from newslynx.exc import RequestError
from newslynx.models import Tag
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.models.util import get_table_columns
from newslynx.views.util import *

# blueprint
bp = Blueprint('tags', __name__)


@bp.route('/api/v1/tags', methods=['GET'])
@load_user
@load_org
def get_tags(user, org):
    """
    Get all tags for an organization.
    """
    # base query
    tag_query = Tag.query.filter_by(organization_id=org.id)

    # optionall filter by type
    type = arg_str('type', default=None)
    if type:
        validate_tag_types(type)
        tag_query = tag_query.filter_by(type=type)

    return jsonify(tag_query.all())


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
