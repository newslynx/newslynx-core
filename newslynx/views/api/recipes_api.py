from flask import Blueprint
from sqlalchemy import func, desc, asc
from pprint import pprint
from collections import defaultdict, Counter

from newslynx.core import db
from newslynx.exc import RequestError
from newslynx.models import Event, Tag, SousChef, Recipe, Thing
from newslynx.models.relations import events_tags, things_events
from newslynx.models.util import get_table_columns
from newslynx.lib.serialize import jsonify
from newslynx.lib import dates
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import *


# blueprint
bp = Blueprint('recipes', __name__)


# utils

@bp.route('/api/v1/recipes', methods=['GET'])
@load_user
@load_org
def search_recipes(user, org):

    # optionally filter by type/level/category
    status = arg_str('status', default=None)
    scheduled = arg_bool('scheduled', default=None)
    sort_field, direction = arg_sort('sort', default=None)
    include_sous_chefs, exclude_sous_chefs = \
        arg_list('sous_chefs', default=[], typ=str, exclusions=True)

    # validate sort fields are part of Recipe object.
    if sort_field:
        validate_fields(Recipe, sort_field, 'to sort by')

    # base query
    recipe_query = db.session.query(Recipe)\
        .filter_by(org_id=org.id)

    # apply filters
    if status:
        recipe_query = recipe_query\
            .filter_by(status=status)

    if len(include_sous_chefs):
        recipe_query = recipe_query\
            .filter(Recipe.sous_chef.has(SousChef.name.in_(include_sous_chefs)))

    if len(exclude_sous_chefs):
        recipe_query = recipe_query\
            .filter(~Recipe.sous_chef.has(SousChef.name.in_(exclude_sous_chefs)))

    if scheduled is not None:
        recipe_query = recipe_query\
            .filter_by(scheduled=scheduled)

    if sort_field:
        sort_obj = eval('Recipe.{}.{}'.format(sort_field, direction))
        recipe_query = recipe_query.order_by(sort_obj())

    # process query, compute facets.
    clean_recipes = []
    facets = defaultdict(Counter)
    for r in recipe_query.all():
        facets['statuses'][r.status] += 1
        facets['sous_chefs'][r.sous_chef.name] += 1
        if r.scheduled:
            facets['schedules']['scheduled'] += 1
        else:
            facets['schedules']['unscheduled'] += 1
        recipe = r.to_dict()
        recipe['event_count'] = r.events.count()
        recipe['thing_count'] = r.things.count()
        clean_recipes.append(recipe)

    resp = {
        'facets': facets,
        'recipes': clean_recipes
    }
    return jsonify(resp)
