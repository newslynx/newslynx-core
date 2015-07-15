from flask import Blueprint, Response
from slugify import slugify

from newslynx.core import db
from newslynx.models import Report
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify, json_to_obj
from newslynx.exc import RequestError, NotFoundError
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import (
    request_data, delete_response, arg_int, arg_str)
from newslynx.constants import TRUE_VALUES
from newslynx.lib import doc

# bp
bp = Blueprint('reports', __name__)


@bp.route('/api/v1/reports', methods=['GET'])
@load_user
@load_org
def org_reports(user, org):
    """
    Returns a list of avaible reports for an organization.
    TODO: Pagination.
    """
    return jsonify(org.reports)


@bp.route('/api/v1/reports', methods=['POST'])
@load_user
@load_org
def create_report(user, org):

    # get the request data
    req_data = request_data()

    name = req_data.get('name')
    slug = req_data.get('slug')
    data = req_data.get('data')
    template_id = req_data.get('template_id', arg_int('template_id', default=None))

    if not name or not data or not template_id:
        raise RequestError(
            "You must pass in 'name', 'data', and  a 'template_id' to create a report. "
            "You only passed in: {}"
            .format(", ".join(req_data.keys())))
    
    if not isinstance(data, (list, dict)):
        try:
            data = json_to_obj(data)
        except Exception as e:
            raise RequestError(
                'Report data could not be parsed: {}'
                .format(e.message))

    r = Report(
        org_id=org.id,
        name=name,
        data=data,
        template_id=template_id)
    
    if slug:
        r.slug = slug

    db.session.add(r)

    # no duplicates.
    try:
        db.session.commit()
    except Exception as e:
        raise RequestError(e.message)
    return jsonify(r)


@bp.route('/api/v1/reports/<id>.<format>', methods=['GET'])
@load_user
@load_org
def get_report(user, org, id, format):

    r = Report.query.filter_by(id=id, org_id=org.id).first()
    if not r:
        raise NotFoundError(
            'Report "{}" does not yet exist for Org "{}"'
            .format(id, org.name))

    # handle format aliases
    if format == "opendocument":
        format = "odt"

    if not r.has_template and format != "json":
        raise RequestError(
            'This report is not associated with a template '
            'so it can only be rendered as json.')

    # handle simple types
    if format == "json":
        return jsonify(r)

    # html
    if format == 'html' and r.template.format == "html":
        return Response(r.render())

    # markdown to html
    elif format == 'html' and r.template.format == "md":
        contents = doc.convert(r.render(), "md", "html")
        return Response(contents)

    # conversions.
    try:
        resp = doc.convert_response(r.render(), r.template.format, format)
    except Exception as e:
        raise RequestError(e.message)
    h = 'inline; filename="{}"'.format(r.filename(format))
    resp.headers['Content-Disposition'] = h
    return resp


@bp.route('/api/v1/reports/<id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_report(user, org, id):

    r = Report.query.filter_by(id=id, org_id=org.id).first()
    if not r:
        raise NotFoundError(
            'Report "{}" does not yet exist for Org "{}"'
            .format(id, org.name))

    # get the request data
    req_data = request_data()

    name = req_data.get('name')
    slug = req_data.get('slug')
    data = req_data.get('data')
    template_id = arg_int('template_id', default=req_data.get('template_id', None))

    if data and not isinstance(data, (list, dict)):
        try:
            data = json_to_obj(data)
        except Exception as e:
            raise RequestError(
                'Report data could not be parsed: {}'
                .format(e.message))
    if name:
        r.name = name
    if slug:
        r.slug = slug
    elif name:
        r.slug = slugify(name)
    if data:
        r.data = data
    if template_id:
        r.template_id = template_id

    # no duplicates.
    try:
        db.session.add(r)
        db.session.commit()
    except Exception as e:
        raise RequestError(e.message)
    return jsonify(r)


@bp.route('/api/v1/reports/<id>', methods=['DELETE'])
@load_user
@load_org
def delete_report(user, org, id):

    r = Report.query.filter_by(id=id, org_id=org.id).first()
    if not r:
        raise NotFoundError(
            'Report "{}" does not yet exist for Org "{}"'
            .format(id, org.name))
    db.session.delete(r)
    db.session.commit()
    return delete_response()

