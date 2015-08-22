from flask import Blueprint
from sqlalchemy import update, and_

from newslynx.core import db
from newslynx.models import Author, ContentItem
from newslynx.models.relations import content_items_authors
from newslynx.models.util import get_table_columns, fetch_by_id_or_field
from newslynx.lib.serialize import jsonify
from newslynx.exc import NotFoundError, RequestError
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import (
    request_data, delete_response,
    arg_bool, arg_str)


# bp
bp = Blueprint('authors', __name__)


@bp.route('/api/v1/authors', methods=['GET'])
@load_user
@load_org
def list_authors(user, org):
    """
    Get all authors.
    """
    incl_content = arg_bool('incl_content', default=False)
    q = arg_str('q', default=None)

    authors = Author.query\
        .filter_by(org_id=org.id)
    if q:
        authors = authors.search(q, vector=Author.search_vector, sort=True)

    return jsonify([a.to_dict(incl_content=incl_content) for a in authors.all()])


@bp.route('/api/v1/authors', methods=['POST'])
@load_user
@load_org
def create_author(user, org):
    """
    Create an author.
    """
    req_data = request_data()
    cols = get_table_columns(Author)
    if 'name' not in req_data:
        raise RequestError(
            "A 'name' is required to create an Author.")

    for k in req_data.keys():
        if k not in cols or k in ['id', 'org_id']:
            req_data.pop(k, None)

        # upper-case.
        elif k == 'name':
            req_data[k] = req_data[k].upper()

    a = Author(org_id=org.id, **req_data)

    try:
        db.session.add(a)
        db.session.commit()

    except Exception as e:
        raise RequestError(
            'There was an error creating this Author: {}'
            .format(e.message))
    return jsonify(a)


@bp.route('/api/v1/authors/<author_id>', methods=['GET'])
@load_user
@load_org
def get_author(user, org, author_id):
    """
    Get an author.
    """
    incl_content = arg_bool('incl_content', default=False)
    a = fetch_by_id_or_field(Author, 'name', author_id,
                             org_id=org.id, transform='upper')
    if not a:
        raise NotFoundError(
            'Author with ID/Name "{}" does not exist."'
            .format(author_id))
    return jsonify(a.to_dict(incl_content=incl_content))


@bp.route('/api/v1/authors/<author_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_author(user, org, author_id):
    """
    Update an author.
    """

    a = fetch_by_id_or_field(Author, 'name', author_id,
                             org_id=org.id, transform='upper')
    if not a:
        raise NotFoundError(
            'Author with ID/Name "{}" does not exist."'
            .format(author_id))

    req_data = request_data()

    cols = get_table_columns(Author)
    for k in req_data.keys():
        if k not in cols or k in ['id', 'org_id']:
            req_data.pop(k, None)

    for k, v in req_data.items():
        if k == 'name':
            if v:
                v = v.upper()
        setattr(a, k, v)

    db.session.add(a)
    db.session.commit()
    return jsonify(a)


@bp.route('/api/v1/authors/<author_id>', methods=['DELETE'])
@load_user
@load_org
def delete_author(user, org, author_id):
    """
    Delete an author.
    """
    a = fetch_by_id_or_field(Author, 'name', author_id,
                             org_id=org.id, transform='upper')
    if not a:
        raise NotFoundError(
            'Author with ID/Name "{}" does not exist."'
            .format(author_id))

    db.session.delete(a)
    db.session.commit()
    return delete_response()


@bp.route('/api/v1/authors/<author_id>/content/<int:content_item_id>',
          methods=['PUT'])
@load_user
@load_org
def author_add_content(user, org, author_id, content_item_id):
    """
    Add an author to a content item.
    """
    a = fetch_by_id_or_field(Author, 'name', author_id,
                             org_id=org.id, transform='upper')
    if not a:
        raise NotFoundError(
            'Author with ID/Name "{}" does not exist."'
            .format(author_id))

    c = ContentItem.query\
        .filter_by(id=content_item_id, org_id=org.id)\
        .first()
    if not c:
        raise RequestError(
            'ContentItem with ID {} does not exist.'
            .format(content_item_id))

    if a.id not in c.author_ids:
        c.authors.append(a)

    db.session.add(c)
    db.session.commit()
    # return modified author
    return jsonify(a.to_dict(incl_content=True))


@bp.route('/api/v1/authors/<author_id>/content/<int:content_item_id>',
          methods=['DELETE'])
@load_user
@load_org
def author_remove_content(user, org, author_id, content_item_id):
    """
    Remove an author from a content item.
    """
    a = fetch_by_id_or_field(Author, 'name', author_id,
                             org_id=org.id, transform='upper')
    if not a:
        raise NotFoundError(
            'Author with ID/Name "{}" does not exist."'
            .format(author_id))

    c = ContentItem.query\
        .filter_by(id=content_item_id, org_id=org.id)\
        .first()

    if not c:
        raise RequestError(
            'ContentItem with ID {} does not exist.'
            .format(content_item_id))

    if a.id in c.author_ids:
        a.content_items.remove(c)

    db.session.add(a)
    db.session.commit()
    return delete_response()


@bp.route('/api/v1/authors/<int:from_author_id>/merge/<int:to_author_id>', methods=['PUT'])
@load_user
@load_org
def merge_authors(user, org, from_author_id, to_author_id):
    """
    Merge two authors.
    """
    from_a = fetch_by_id_or_field(Author, 'name', from_author_id,
                                  org_id=org.id, transform='upper')
    if not from_a:
        raise NotFoundError(
            'Author with ID/Name "{}" does not exist."'
            .format(from_author_id))

    to_a = fetch_by_id_or_field(Author, 'name', to_author_id,
                                org_id=org.id, transform='upper')
    if not to_a:
        raise NotFoundError(
            'Author with ID/Name "{}" does not exist."'
            .format(to_author_id))

    # re associate content
    stmt = update(content_items_authors)\
        .where(and_(
            content_items_authors.c.author_id == from_author_id,
            ~content_items_authors.c.content_item_id.in_(to_a.content_item_ids)))\
        .values(author_id=to_author_id)

    db.session.execute(stmt)

    # remove from author id
    db.session.delete(from_a)
    db.session.commit()

    return jsonify(to_a.to_dict(incl_content=True))
