import copy
import pickle

from sqlalchemy.dialects.postgresql import JSON, ENUM
from slugify import slugify

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.stats import parse_number
from newslynx.lib.search import SearchString
from newslynx.exc import RecipeSchemaError, SearchStringError
from newslynx.constants import RECIPE_STATUSES
from newslynx.util import gen_hash_id


RECIPE_SCHEMA_MAP = {
    "boolean": bool,
    "datetime": dates.parse_iso,
    "searchstring": SearchString,
    "text": unicode,
    "number": parse_number,
    "list": list
}


def validate_recipe(sous_chef, recipe, uninitialized=False):
    """
    Given a sous_chef schema, validate one of it's recipes.
    """
    parsed_options = {}
    recipe_options = recipe.get('options', {})
    for name, value in sous_chef['options'].iteritems():
        opt = recipe_options.get(name, None)
        raw = copy.copy(opt)

        # check for required values:
        if opt is None:
            if value.get('required', False):

                # if the recipe is a default, aka unintialized,
                # simply ignore requirements
                if uninitialized:
                    opt = None

                else:
                    raise RecipeSchemaError(
                        "Recipes associated with SousChef '{}' require a '{}' option."
                        .format(sous_chef['name'], name))
            else:
                opt = value.get('default', None)

        typ = value['type']

        if opt:

            # check for proper types
            type_fn = RECIPE_SCHEMA_MAP[typ]

            # custom first:
            if typ == 'datetime':
                opt = type_fn(opt)
                if not opt:
                    raise RecipeSchemaError(
                        "{} is an datetime field but was passed '{}'."
                        .format(name, raw))

            elif typ == 'searchstring':
                try:
                    opt = type_fn(opt)
                except SearchStringError as e:
                    raise RecipeSchemaError(e.message)

            elif typ == 'boolean':
                if isinstance(opt, basestring):
                    opt = opt.lower() in ['y', 'yes', '1', 't', 'true', 'ok']
                else:
                    try:
                        opt = type_fn(opt)
                    except:
                        raise RecipeSchemaError(
                            "{} is an boolean field but was passed '{}'."
                            .format(name, raw))

            elif typ == 'list':
                if not isinstance(opt, list):
                    raise RecipeSchemaError(
                        "{} is a {} field but was passed '{}'."
                        .format(name, typ, raw))
            else:
                try:
                    opt = type_fn(opt)

                except:
                    raise RecipeSchemaError(
                        "{} is a {} field but was passed '{}'."
                        .format(name, typ, raw))

        # deal with serialization problems
        if typ in ['searchstring', 'datetime']:
            recipe['options'][name] = raw
        else:
            recipe['options'][name] = opt

        # save parsed options
        parsed_options[name] = opt

        # get scheduler fields
        if name in ['time_of_day', 'interval']:
            recipe[name] = opt
            recipe['options'][name] = opt
            parsed_options[name] = opt

    # fallback on sous-chef defaults for recipe's name, slug, and description.
    for name in ['name', 'description', 'slug']:
        if name not in recipe or not recipe.get(name):
            if name != 'slug':
                recipe[name] = sous_chef[name]
                recipe['options'][name] = sous_chef[name]
                parsed_options[name] = sous_chef[name]

            # randomize recipe slug.
            else:
                slug = "{}-{}".format(sous_chef[name], gen_hash_id())
                recipe['options'][name] = slug
                recipe[name] = slug

    return recipe, parsed_options


class Recipe(db.Model):

    __tablename__ = 'recipes'

    # id fields
    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    sous_chef_id = db.Column(
        db.Integer, db.ForeignKey('sous_chefs.id'), index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), index=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)

    # metadata fields
    name = db.Column(db.Text, index=True)
    slug = db.Column(db.Text, index=True)
    description = db.Column(db.Text)

    # date fields
    created = db.Column(db.DateTime(timezone=True), index=True)
    updated = db.Column(db.DateTime(timezone=True), index=True)
    last_run = db.Column(db.DateTime(timezone=True), index=True)

    # scheduler fields
    scheduled = db.Column(db.Boolean, index=True)
    time_of_day = db.Column(db.Text, index=True)
    interval = db.Column(db.Integer, index=True)
    status = db.Column(
        ENUM(*RECIPE_STATUSES, name="enum_recipe_statuses"), index=True)
    last_job = db.Column(JSON)

    # options
    options = db.Column(JSON)
    pickle_opts = db.Column(db.Text)

    # relations
    events = db.relationship(
        'Event', backref=db.backref('recipe', lazy='joined'), lazy='dynamic')
    things = db.relationship(
        'Thing', backref=db.backref('recipe', lazy='joined'), lazy='dynamic')
    metrics = db.relationship(
        'Metric', backref=db.backref('recipe', lazy='joined'), lazy='dynamic')
    sous_chef = db.relationship(
        'SousChef', backref=db.backref('recipes', lazy='joined'), lazy='joined')
    user = db.relationship(
        'User', backref=db.backref('recipes', lazy='dynamic'), lazy='joined')

    __table_args__ = (
        db.UniqueConstraint('org_id', 'slug'),
    )

    def __init__(self, sous_chef, **recipe):
        """
        A recipe must be initialized with an existing sous chef.
        """
        status = recipe.get('status')
        sc = sous_chef.to_dict()
        kw, parsed_options = validate_recipe(
            sc, recipe, status == 'uninitialized')

        self.sous_chef_id = sous_chef.id
        self.user_id = kw.get('user_id')
        self.org_id = kw.get('org_id')
        self.name = kw.get('name')
        self.slug = slugify(kw.get('slug', kw['name']))
        self.description = kw.get('description')
        self.created = kw.get('created', dates.now())
        self.updated = kw.get('updated', dates.now())
        self.last_run = kw.get('last_run', None)

        if not (kw.get('time_of_day') or kw.get('interval')) \
                or status == 'uninitialized':
            sched = False
        else:
            sched = True

        self.scheduled = kw.get('scheduled', sched)
        self.time_of_day = kw.get('time_of_day')
        self.interval = kw.get('interval')
        self.status = kw.get('status')
        self.last_job = kw.get('last_job', {})
        self.options = kw.get('options', {})

        # keep internally parsed options
        self.pickle_opts = pickle.dumps(parsed_options)

    def to_dict(self, incl_sous_chef=False):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'sous_chef_id': self.sous_chef.id,
            'sous_chef_slug': self.sous_chef.slug,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'created': self.created,
            'updated': self.updated,
            'last_run': self.last_run,
            'scheduled': self.scheduled,
            'time_of_day': self.time_of_day,
            'interval': self.interval,
            'status': self.status,
            'last_job': self.last_job,
            'options': pickle.loads(self.pickle_opts)
        }

    def __repr__(self):
        return '<Recipe %r >' % (self.slug)
