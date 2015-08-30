"""
Load defaults for an Organization from configurations.
"""
import logging

from newslynx import init
from newslynx.lib.text import slug
from newslynx.core import db
from newslynx.exc import RecipeSchemaError
from newslynx.models import (
    Org, User, Tag, Report, SousChef,
    Metric, Recipe, Event,
    recipe_schema, sous_chef_schema
)
from newslynx.core import settings


log = logging.getLogger(__name__)


def org(
        name=settings.SUPER_USER_ORG,
        timezone=settings.SUPER_USER_ORG_TIMEZONE,
        email=settings.SUPER_USER_EMAIL):

    # create the org and super user
    org = Org.query.filter_by(name=name).first()
    if not org:
        log.info('Creating org: "{}"'.format(name))
        org = Org(name=name, timezone=timezone)
    else:
        log.warning('Updating org: "{}"'.format(name))
        org.timezone = timezone
        org.name = name
        org.slug = slug(unicode(name))

    # create the super user and add to the org.
    u = User.query.filter_by(email=email).first()
    if not u:
        log.info('Creating super user: "{}"'.format(email))
        u = User(name=settings.SUPER_USER,
                 email=settings.SUPER_USER_EMAIL,
                 password=settings.SUPER_USER_PASSWORD,
                 admin=True,
                 super_user=True)
        u.apikey = settings.SUPER_USER_APIKEY

    else:
        log.warning('Updating super user: "{}"'.format(email))
        u.apikey = settings.SUPER_USER_APIKEY
        u.email = settings.SUPER_USER_EMAIL
        u.password = settings.SUPER_USER_PASSWORD
        u.admin = True
        u.super_user = True
    org.users.append(u)
    db.session.add(org)
    db.session.commit()
    tags(org)
    sous_chefs(org)
    recipes(org)
    return org


def tags(org):
    """
    (Re)load all default tags.
    """
    # add default tags
    for tag in init.load_default_tags():
        tag['org_id'] = org.id
        t = Tag.query\
            .filter_by(org_id=tag['org_id'], slug=tag['slug'], type=tag['type'])\
            .first()
        if not t:
            log.info('Creating tag: "{slug}"'.format(**tag))
            t = Tag(**tag)
        else:
            log.warning('Updating tag: "{slug}"'.format(**tag))
            for k, v in tag.items():
                setattr(t, k, v)
        db.session.add(t)
    db.session.commit()
    return org


def sous_chefs(org):
    """
    (Re)load all sous chefs.
    """
    # load all sous-chefs
    for sc, fp in init.load_sous_chefs():
        sc = sous_chef_schema.validate(sc, fp)
        sc['org_id'] = org.id
        sc_obj = db.session.query(SousChef).filter_by(
            slug=sc['slug']).first()
        if not sc_obj:
            log.info('Creating sous chef: "{slug}"'.format(**sc))
            sc_obj = SousChef(**sc)
        else:
            log.warning('Updating sous chef: "{slug}"'.format(**sc))
            sc = sous_chef_schema.update(sc_obj.to_dict(), sc)
            for name, value in sc.items():
                setattr(sc_obj, name, value)
        db.session.add(sc_obj)
    db.session.commit()
    return org


def recipes(org):
    """
    (Re)load all default recipes.
    """
    # add default recipes
    for recipe in init.load_default_recipes():

        # fetch it's sous chef.
        sous_chef_slug = recipe.pop('sous_chef')
        if not sous_chef_slug:
            raise RecipeSchemaError(
                "Default recipe '{}' is missing a 'sous_chef' slug."
                .format(recipe.get('slug', '')))
        sc = SousChef.query\
            .filter_by(slug=sous_chef_slug, org_id=org.id)\
            .first()
        if not sc:
            raise RecipeSchemaError(
                '"{}" is not a valid SousChef slug or the '
                'SousChef does not yet exist for "{}"'
                .format(sous_chef_slug, org.slug))

        # validate the recipe
        recipe = recipe_schema.validate(recipe, sc.to_dict())

        # fill in relations
        recipe['user_id'] = org.super_user.id
        recipe['org_id'] = org.id

        r = Recipe.query\
            .filter_by(org_id=org.id, name=recipe['name'])\
            .first()

        if not r:
            log.info('Creating recipe: "{slug}"'.format(**recipe))
            # add to database here.
            r = Recipe(sc, **recipe)
        else:
            log.warning('Updating recipe: "{slug}"'.format(**recipe))
            for name, value in recipe.items():
                if name != 'options':
                    setattr(r, name, value)
                else:
                    r.set_options(value)

        db.session.add(r)
        db.session.commit()

        # if the recipe creates metrics create them here.
        if 'metrics' in sc.creates and r.status == 'stable':
            for name, params in sc.metrics.items():
                m = Metric.query\
                    .filter_by(org_id=org.id, recipe_id=r.id, name=name, type=params['type'])\
                    .first()
                # print "METRICS PARAMS", params
                if not m:
                    log.info('Creating metric: "{}"'.format(name))
                    m = Metric(
                        name=name,
                        recipe_id=r.id,
                        org_id=org.id,
                        **params)

                else:
                    log.warning('Updating metric: "{}"'.format(name))
                    for k, v in params.items():
                        setattr(m, k, v)

                db.session.add(m)
        db.session.commit()

    return org
