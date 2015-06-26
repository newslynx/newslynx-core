from collections import defaultdict, Counter

from sqlalchemy import or_
from flask import Blueprint

from newslynx.core import db
from newslynx.exc import RequestError, ConflictError
from newslynx.models import SousChef, Recipe, Metric
from newslynx.models import recipe_schema
from newslynx.models.util import fetch_by_id_or_field
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import *
from newslynx.tasks import facet
from newslynx.merlynne import Merlynne


# blueprint
bp = Blueprint('recipes', __name__)

# utils


@bp.route('/api/v1/recipes', methods=['GET'])
@load_user
@load_org
def list_recipes(user, org):

    # optionally filter by type/level/category
    include_statuses, exclude_statuses = \
        arg_list('status', default=[], typ=str, exclusions=True)
    include_creates, exclude_creates = \
        arg_list('creates', default=[], typ=str, exclusions=True)
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

    # include statuses
    if len(include_statuses):
        validate_recipe_statuses(include_statuses)
        recipe_query = recipe_query\
            .filter(Recipe.status.in_(include_statuses))

    # exclude statuses
    if len(exclude_statuses):
        validate_recipe_statuses(exclude_statuses)
        recipe_query = recipe_query\
            .filter(~Recipe.status.in_(exclude_statuses))

    # include creates
    if len(include_creates):
        validate_sous_chef_creates(include_creates)
        recipe_query = recipe_query\
            .filter(Recipe.sous_chef.has(SousChef.creates.in_(include_creates)))

    # exclude creates
    if len(exclude_creates):
        validate_sous_chef_creates(exclude_creates)
        recipe_query = recipe_query\
            .filter(~Recipe.sous_chef.has(SousChef.creates.in_(exclude_creates)))

    # include sous chefs
    if len(include_sous_chefs):
        recipe_query = recipe_query\
            .filter(Recipe.sous_chef.has(SousChef.slug.in_(include_sous_chefs)))

    # exclude sous chefs
    if len(exclude_sous_chefs):
        recipe_query = recipe_query\
            .filter(~Recipe.sous_chef.has(SousChef.slug.in_(exclude_sous_chefs)))

    if len(include_recipes):
        slugs = []
        ids = []
        for r in include_recipes:
            try:
                i = parse_number(r)
                ids.append(i)
            except:
                slugs.append(r)

        recipe_query = recipe_query\
            .filter(or_(Recipe.id.in_(ids), Recipe.slug.in_(slugs)))

    if len(exclude_recipes):
        slugs = []
        ids = []
        for r in exclude_recipes:
            try:
                i = parse_number(r)
                ids.append(i)
            except:
                slugs.append(r)

        recipe_query = recipe_query\
            .filter(~or_(Recipe.id.in_(ids), Recipe.slug.in_(slugs)))

    if scheduled is not None:
        recipe_query = recipe_query\
            .filter_by(schedule_by is not None)

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

        if r.schedule_by == 'unscheduled':
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
            'You must pass in a SousChef ID or slug to create a recipe.')

    sc = fetch_by_id_or_field(SousChef, 'slug', sous_chef)
    if not sc:
        raise RequestError(
            'A SousChef does not exist with ID/slug {}'
            .format(sous_chef))

    # validate the recipe and add it to the database.
    recipe = recipe_schema.validate(req_data, sc.to_dict())
    r = Recipe(sc, user_id=user.id, org_id=org.id, **recipe)
    db.session.add(r)
    db.session.commit()

    # if the recipe creates metrics create them in here.
    if 'metrics' in sc.creates:
        for name, params in sc.metrics.items():
            m = Metric(
                name=name,
                recipe_id=r.id,
                org_id=org.id,
                **params)
            db.session.add(m)
    try:
        db.session.commit()

    except Exception as e:
        raise ConflictError(
            "You tried to create a metric that already exists. "
            "Here's the exact error:\n{}"
            .format(e.message)
        )

    return jsonify(r)


@bp.route('/api/v1/recipes/<recipe_id>', methods=['GET'])
@load_user
@load_org
def get_recipe(user, org, recipe_id):
    r = fetch_by_id_or_field(Recipe, 'slug', recipe_id, org_id=org.id)
    if not r:
        raise RequestError('Recipe with id/slug {} does not exist.'
                           .format(recipe_id))

    # add in event counts.
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
        # just delete recipes with no approved events.
        event_cnt = r.events.filter_by(status='approved').count()
        if event_cnt > 0:
            r.status = 'inactive'
            db.session.add(r)
        else:
            db.session.delete(r)

    # set the status of associated events to 'deleted'
    cmd = """
    UPDATE events SET status='deleted' WHERE recipe_id = {} AND status='pending';
    """.format(r.id)
    db.session.execute(cmd)
    db.session.commit()

    return delete_response()


@bp.route('/api/v1/recipes/<recipe_id>/cook', methods=['GET', 'POST'])
@load_user
@load_org
def cook_a_recipe(user, org, recipe_id):
    """
    Run recipes via the API.
    """
    r = fetch_by_id_or_field(Recipe, 'slug', recipe_id, org_id=org.id)
    if not r:
        raise RequestError('Recipe with id/slug {} does not exist.'
                           .format(recipe_id))

    # setup kwargs for merlynne
    kw = dict(
        org=org.to_dict(
            incl_auths=True,
            auths_as_dict=True,
            settings_as_dict=True,
            incl_domains=True,
            incl_users=True),
        apikey=user.apikey,
        recipe=r.to_dict(),
        recipe_obj=r,
        sous_chef_path=r.sous_chef.runs)

    # cook recipe
    merlynne = Merlynne(**kw)
    try:
        job_id = merlynne.cook_recipe()
    except Exception as e:
        raise RequestError(
            'There was a problem initializing the SousChef: {}'
            .format(e.message))

    # # return job status url
    ret = url_for_job_status(apikey=user.apikey, job_id=job_id, queue='recipe')
    return jsonify(ret, status=202)
