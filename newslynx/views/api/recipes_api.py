from collections import defaultdict, Counter

from flask import Blueprint

from newslynx.core import db
from newslynx.exc import RequestError
from newslynx.models import SousChef, Recipe
from newslynx.models.recipe import validate_recipe
from newslynx.models.util import get_table_columns, fetch_by_id_or_field
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
def list_recipes(user, org):

    # optionally filter by type/level/category
    status = arg_str('status', default=None)
    scheduled = arg_bool('scheduled', default=None)
    sort_field, direction = arg_sort('sort', default='-created')
    include_sous_chefs, exclude_sous_chefs = \
        arg_list('sous_chefs', default=[], typ=str, exclusions=True)

    # validate sort fields are part of Recipe object.
    if sort_field:
        validate_fields(Recipe, [sort_field], 'to sort by')

    # base query
    recipe_query = db.session.query(Recipe)\
        .filter_by(org_id=org.id)

    # apply filters
    if status:
        recipe_query = recipe_query\
            .filter_by(status=status)

    if len(include_sous_chefs):
        recipe_query = recipe_query\
            .filter(Recipe.sous_chef.has(SousChef.slug.in_(include_sous_chefs)))

    if len(exclude_sous_chefs):
        recipe_query = recipe_query\
            .filter(~Recipe.sous_chef.has(SousChef.slug.in_(exclude_sous_chefs)))

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
        facets['sous_chefs'][r.sous_chef.slug] += 1
        facets['creates'][r.sous_chef.creates] += 1
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


@bp.route('/api/v1/recipes', methods=['POST'])
@load_user
@load_org
def create_recipe(user, org):

    req_data = request_data()

    sous_chef = req_data.pop('sous_chef', arg_str('sous_chef', None))
    if not sous_chef:
        raise RequestError(
            'You must pass in a sous_chef ID or slug to create a recipe')

    sc = fetch_by_id_or_field(SousChef, 'slug', sous_chef)
    if not sc:
        raise RequestError(
            'A SousChef does not exist with ID/slug {}'.format(sous_chef))

    r = Recipe(sc, **req_data)
    db.session.add(r)
    db.session.commit()

    return jsonify(r)


@bp.route('/api/v1/recipes/<recipe_id>', methods=['GET'])
@load_user
@load_org
def get_recipe(user, org, recipe_id):
    r = fetch_by_id_or_field(Recipe, 'slug', recipe_id, org_id=org.id)
    if not r:
        raise RequestError('Recipe with id/slug {} does not exist.'
                           .format(recipe_id))
    return jsonify(r)


@bp.route('/api/v1/recipes/<recipe_id>', methods=['PUT'])
@load_user
@load_org
def update_recipe(user, org, recipe_id):

    r = fetch_by_id_or_field(Recipe, 'slug', recipe_id, org_id=org.id)
    if not r:
        raise RequestError('Recipe with id/slug {} does not exist.'
                           .format(recipe_id))

    req_data = request_data()

    # split out non schema fields:
    non_schema = [
        'id', 'sous_chef_id', 'user_id', 'org_id',
        'last_run', 'status', 'created', 'updated',
        'scheduled', 'last_run', 'status', 'last_job'
    ]
    for k in non_schema:
        req_data.pop(k, None)

    recipe, parsed_options = validate_recipe(
        r.sous_chef.to_dict(), req_data)

    cols = get_table_columns(Recipe)
    for name, value in recipe.items():
        if name in cols:
            setattr(r, name, value)

    # initialize default recipes
    if r.status == 'unititialized':
        r.status = 'stable'

    # set updated time.
    r.updated = dates.now()

    # update pickled options
    r.set_pickle_opts(parsed_options)

    db.session.add(r)
    db.session.commit()

    return jsonify(r)
