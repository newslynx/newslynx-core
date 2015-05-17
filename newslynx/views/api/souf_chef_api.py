from collections import defaultdict, Counter

from flask import Blueprint

from newslynx.core import db
from newslynx.models import SousChef
from newslynx.models.sous_chef import validate_sous_chef
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.models.util import fetch_by_id_or_field
from newslynx.views.util import *


# blueprint
bp = Blueprint('sous_chefs', __name__)


# utils

@bp.route('/api/v1/sous-chefs', methods=['GET'])
@load_user
@load_org
def list_sous_chefs(user, org):

    # optionally filter by type/level/category
    creates = arg_str('creates', default='all')
    is_command = arg_bool('is_command', default=None)

    # base query
    sous_chef_query = db.session.query(SousChef)

    # apply filters
    if creates != "all":
        sous_chef_query = sous_chef_query\
            .filter_by(creates=creates)

    if is_command is not None:
        sous_chef_query = sous_chef_query\
            .filter_by(is_command=is_command)

    # process query, compute facets.
    clean_sous_chefs = []
    facets = defaultdict(Counter)
    for sc in sous_chef_query.all():
        facets['creates'][sc.creates] += 1
        if not sc.is_command:
            facets['runners']['python'] += 1
        else:
            facets['runners']['command'] += 1
        clean_sous_chefs.append(sc)

    resp = {
        'facets': facets,
        'sous_chefs': clean_sous_chefs
    }
    return jsonify(resp)


@bp.route('/api/v1/sous-chefs', methods=['POST'])
@load_user
@load_org
def create_sous_chef(user, org):

    req_data = request_data()

    # inititializing a sous chef effectively validates it.
    sc = SousChef(**req_data)
    db.session.add(sc)
    try:
        db.session.commit()
    except Exception as e:
        raise RequestError(e.message)

    return jsonify(sc)


@bp.route('/api/v1/sous-chefs/<sous_chef>', methods=['GET'])
@load_user
@load_org
def get_sous_chef(user, org, sous_chef):

    sc = fetch_by_id_or_field(SousChef, 'slug', sous_chef)
    if not sc:
        raise NotFoundError(
            'A SousChef does not exist with ID/slug {}'.format(sous_chef))

    return jsonify(sc)


@bp.route('/api/v1/sous-chefs/<sous_chef>', methods=['PUT'])
@load_user
@load_org
def update_sous_chef(user, org, sous_chef):

    sc = fetch_by_id_or_field(SousChef, 'slug', sous_chef)
    if not sc:
        raise NotFoundError(
            'A SousChef does not exist with ID/slug {}'.format(sous_chef))

    req_data = request_data()

    # split out non schema fields:
    for k in ['id', 'is_command']:
        req_data.pop(k, None)

    # validate the schema
    sous_chef = validate_sous_chef(req_data)

    # udpate
    cols = get_table_columns(SousChef)
    for name, value in sous_chef.items():
        if name in cols:
            setattr(sc, name, value)

    db.session.add(sc)
    db.session.commit()

    return jsonify(sc)
