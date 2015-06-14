from collections import defaultdict, Counter

from flask import Blueprint

from newslynx.core import db
from newslynx.exc import RequestError
from newslynx.models import SousChef, Recipe
from newslynx.models import recipe_schema
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import *
from newslynx.tasks import facet


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
    include_recipes, exclude_recipes = \
        arg_list('recipes', default=[], typ=str, exclusions=True)

    # validate sort fields are part of Recipe object.
    if sort_field:
        validate_fields(Recipe, fields=[sort_field], suffix='to sort by')

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

    if len(include_recipes):
        rids = []
        for rid in include_recipes:
            r = fetch_by_id_or_field(Recipe, 'slug', rid, org_id=org.id)
            if not r:
                raise RequestError(
                    'A recipe with ID/slug {} does not exist.'
                    .format(rid))
            rids.append(r.id)

        recipe_query = recipe_query\
            .filter(Recipe.id.in_(rids))

    if len(exclude_recipes):
        rids = []
        for rid in exclude_recipes:
            r = fetch_by_id_or_field(Recipe, 'slug', rid, org_id=org.id)
            if not r:
                raise RequestError(
                    'A recipe with ID/slug {} does not exist.'
                    .format(rid))
            rids.append(r.id)

        recipe_query = recipe_query\
            .filter(~Recipe.id.in_(include_recipes))

    if scheduled is not None:
        recipe_query = recipe_query\
            .filter_by(scheduled=scheduled)

    if sort_field:
        sort_obj = eval('Recipe.{}.{}'.format(sort_field, direction))
        recipe_query = recipe_query.order_by(sort_obj())

    # get all recipe ids:
    recipe_ids = [re[0] for re in recipe_query.with_entities(Recipe.id).all()]

    event_count_lookup = facet.event_statuses_by_recipes(recipe_ids)

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
        recipe['event_counts'] = event_count_lookup.get(recipe['id'])
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

    # validate the recipe and add it to the database.
    recipe = recipe_schema.validate(req_data, sc.to_dict())
    r = Recipe(sc, user_id=user.id, org_id=org.id, **recipe)
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


@bp.route('/api/v1/recipes/<recipe_id>', methods=['PUT', 'PATCH'])
@load_user
@load_org
def update_recipe(user, org, recipe_id):

    r = fetch_by_id_or_field(Recipe, 'slug', recipe_id, org_id=org.id)
    if not r:
        raise RequestError('Recipe with id/slug {} does not exist.'
                           .format(recipe_id))

    # fetch request date and update / validate.
    req_data = request_data()
    new_recipe = recipe_schema.update(r, req_data, r.sous_chef.to_dict())

    # if the requesting user hasn't initializied this recipe,
    # do it for them:
    status = new_recipe.get('status', 'uninitialized')
    if r.status == 'uninitialized' and status == 'uninitialized':
        r.status = 'stable'
        new_recipe['status'] = 'stable'

    # update pickled options
    new_opts = new_recipe.pop('options')
    r.set_options(new_opts)

    # update all other fields
    for col, val in new_recipe.items():
        setattr(r, col, val)

    db.session.add(r)
    db.session.commit()

    return jsonify(r)


@bp.route('/api/v1/recipes/<recipe_id>', methods=['DELETE'])
@load_user
@load_org
def delete_recipe(user, org, recipe_id):

    r = fetch_by_id_or_field(Recipe, 'slug', recipe_id, org_id=org.id)
    if not r:
        raise RequestError('Recipe with id/slug {} does not exist.'
                           .format(recipe_id))
    force = arg_bool('force', default=False)
    if force:
        db.session.delete(r)
    else:
        r.status = 'inactive'
        cmd = """
        UPDATE events SET status='deleted' WHERE recipe_id = {} AND status='pending';
        """.format(r.id)
        db.session.execute(cmd)
        db.session.add(r)
    db.session.commit()
    return delete_response()
