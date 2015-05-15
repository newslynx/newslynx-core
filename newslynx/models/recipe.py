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
from newslynx.models.sous_chef import DEFAULT_SOUS_CHEF_OPTIONS


def validate_recipe_opt(name, typ, raw):
    """
    Validate a recipe option
    """

    # custom first:
    if typ == 'datetime':
        opt = dates.parse_iso(raw)
        if not opt:
            raise RecipeSchemaError(
                "{} is an {} field but was passed '{}'."
                .format(name, typ, raw))

    elif typ == 'searchstring':
        try:
            opt = SearchString(raw)
        except SearchStringError as e:
            raise RecipeSchemaError(e.message)

    elif typ == 'boolean':
        if isinstance(raw, basestring):
            opt = raw.lower() in ['y', 'yes', '1', 't', 'true', 'ok']
        else:
            try:
                opt = bool(raw)
            except:
                raise RecipeSchemaError(
                    "{} is an {} field but was passed '{}'."
                    .format(name, typ, raw))

    elif typ == 'list':
        if not isinstance(raw, list):
            raise RecipeSchemaError(
                "{} is a {} field but was passed '{}'."
                .format(name, typ, raw))
        else:
            opt = raw

    elif typ == 'number':
        try:
            opt = parse_number(raw)
        except:
            raise RecipeSchemaError(
                "{} is a {} field but was passed '{}'."
                .format(name, typ, raw))

    elif typ == 'text':
        try:
            opt = raw.decode('utf-8')
        except:
            raise RecipeSchemaError(
                "{} is a {} field but was passed '{}'."
                .format(name, typ, raw))

    return opt


def validate_recipe_sous_chef_defaults(recipe, sous_chef):
    """"
    Merge in sous-chef defaults with recipe.
    """
    for key in DEFAULT_SOUS_CHEF_OPTIONS.keys():
        typ = DEFAULT_SOUS_CHEF_OPTIONS[key].get('type')
        if key in recipe['options']:
            raw = recipe['options'].pop(key)
            recipe[key] = validate_recipe_opt(key, typ, raw)

        elif key in recipe:
            raw = recipe.pop(key)
            recipe[key] = validate_recipe_opt(key, typ, raw)

        else:
            if key != 'slug':
                recipe[key] = sous_chef['options'][key].get('default', None)
            else:
                slug = "{}-{}".format(sous_chef[key], gen_hash_id())
                recipe[key] = slug

    return recipe


def validate_recipe_schedule(recipe, uninitialized=False):
    """
    Validate recipe schedule options.
    """
    # check if recipe has time_of_day and interval
    if recipe.get('time_of_day') and recipe.get('interval'):
        raise RecipeSchemaError(
            'A recipe cannot have "time_of_day" and "interval" set.')

    # check if a recipe should be scheduled.
    if not (recipe.get('time_of_day') or recipe.get('interval')) \
            or uninitialized:
        recipe['scheduled'] = False

    else:
        recipe['scheduled'] = True

    return recipe


def validate_recipe(sous_chef, recipe, uninitialized=False):
    """
    Given a sous_chef schema, validate one of it's recipes.
    """
    # merge default sous chef options into top-level
    # of recipe
    recipe = validate_recipe_sous_chef_defaults(recipe, sous_chef)

    parsed_options = {}

    # validate custom options
    for name, value in sous_chef['options'].iteritems():
        if name not in DEFAULT_SOUS_CHEF_OPTIONS.keys():

            opt = recipe['options'].get(name, None)
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
                opt = validate_recipe_opt(name, typ, opt)

            # deal with serialization problems
            if typ in ['searchstring', 'datetime']:
                recipe['options'][name] = raw
            else:
                recipe['options'][name] = opt

            # save parsed options
            parsed_options[name] = opt

    recipe = validate_recipe_schedule(recipe, uninitialized)

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

        # core fields
        self.name = kw.get('name')
        self.slug = slugify(kw.get('slug', kw['name']))
        self.description = kw.get('description')
        self.time_of_day = kw.get('time_of_day')
        self.interval = kw.get('interval')
        self.options = kw.get('options', {})

        # internal fields
        self.sous_chef_id = sous_chef.id
        self.user_id = kw.get('user_id')
        self.org_id = kw.get('org_id')
        self.created = kw.get('created', dates.now())
        self.updated = kw.get('updated', dates.now())
        self.scheduled = kw.get('scheduled')
        self.last_run = kw.get('last_run', None)
        self.last_job = kw.get('last_job', {})
        self.status = kw.get('status')

        # keep internally parsed options
        self.pickle_opts = pickle.dumps(parsed_options)

    def set_pickle_opts(self, opts):
        self.pickle_opts = pickle.dumps(opts)

    def to_dict(self, incl_sous_chef=False):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'sous_chef': self.sous_chef.slug,
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
