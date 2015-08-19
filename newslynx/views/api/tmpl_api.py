from flask import Blueprint
from jinja2 import Template as Tmpl 

from newslynx.core import db
from newslynx.models import Template
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify, json_to_obj
from newslynx.exc import RequestError, NotFoundError
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import (
    request_data, delete_response)
from newslynx.constants import TRUE_VALUES
from newslynx.lib.text import slug

# bp
bp = Blueprint('templates', __name__)


@bp.route('/api/v1/templates', methods=['GET'])
@load_user
@load_org
def org_templates(user, org):

    return jsonify(org.templates)


@bp.route('/api/v1/templates', methods=['POST'])
@load_user
@load_org
def create_template(user, org):

    # get the request data
    req_data = request_data()

    name = req_data.get('name')
    slug = req_data.get('slug')
    template = req_data.get('template')
    format = req_data.get('format')

    if not name or not template or not format:
        raise RequestError(
            "You must pass in a 'name', 'format', and 'template' to create a template. "
            "You only passed in: {}"
            .format(", ".join(req_data.keys())))
    try:
        t = Tmpl(template)
    except Exception as e:
        raise RequestError('This template is invalid: {}'.format(e.message))

    t = Template(
        org_id=org.id,
        name=name,
        template=template,
        format=format)
    if slug:
        t.slug = slug

    db.session.add(t)

    # no duplicates.
    try:
        db.session.commit()
    except Exception as e:
        raise RequestError(e.message)
    return jsonify(t)


@bp.route('/api/v1/templates/<slug_id>', methods=['GET'])
@load_user
@load_org
def get_template(user, org, slug_id):

    t = fetch_by_id_or_field(Template, 'slug', slug_id, org_id=org.id)
    if not t:
        raise NotFoundError(
            'Template "{}" does not yet exist for Org "{}"'
            .format(slug_id, org.name))
    return jsonify(t)


@bp.route('/api/v1/templates/<slug_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_template(user, org,slug_id):

    t = fetch_by_id_or_field(Template, 'slug', slug_id, org_id=org.id)
    if not t:
        raise NotFoundError(
            'Template "{}" does not yet exist for Org "{}"'
            .format(slug_id, org.name))

    # get the request data
    req_data = request_data()

    name = req_data.get('name')
    slug = req_data.get('slug')
    template = req_data.get('template')
    format = req_data.get('format')
    if name:
        t.name = name
    if slug:
        t.slug = slug
    elif name:
        t.slug = slug(name)
    if template:
        try:
            tmpl = Tmpl(template)
        except Exception as e:
            raise RequestError('This template is invalid: {}'.format(e.message))
        t.template = template
    if format:
        t.format = format

    # no duplicates.
    try:
        db.session.add(t)
        db.session.commit()
    except Exception as e:
        raise RequestError(e.message)
    return jsonify(t)


@bp.route('/api/v1/templates/<slug_id>', methods=['DELETE'])
@load_user
@load_org
def delete_template(user, org, slug_id):

    t = fetch_by_id_or_field(Template, 'slug', slug_id, org_id=org.id)
    if not t:
        raise NotFoundError(
            'Template "{}" does not yet exist for Org "{}"'
            .format(slug_id, org.name))
    db.session.delete(t)
    db.session.commit()
    return delete_response()
