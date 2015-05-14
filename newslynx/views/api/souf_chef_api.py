from flask import Blueprint
from sqlalchemy import func, desc, asc
from pprint import pprint
from collections import defaultdict, Counter

from newslynx.core import db
from newslynx.models import SousChef
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
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
