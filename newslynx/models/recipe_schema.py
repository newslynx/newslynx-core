import re
import copy

from newslynx.lib import dates
from newslynx.lib import url
from newslynx.lib import mail
from newslynx.lib.stats import parse_number
from newslynx.lib.search import SearchString
from newslynx.lib.serialize import obj_to_json, json_to_obj
from newslynx.models import Recipe
from newslynx.util import gen_short_uuid, update_nested_dict
from newslynx.exc import (
    RecipeSchemaError, SearchStringError)
from .sous_chef_schema import *
from newslynx.constants import (
    TRUE_VALUES, FALSE_VALUES, NULL_VALUES,
    RECIPE_REMOVE_FIELDS, RECIPE_INTERNAL_FIELDS,
    RECIPE_SCHEDULE_METHODS
)

# order type checking from most to least
# finnicky
TYPE_SORT_ORDER = {
    "email": 1,
    "url": 2,
    "crontab": 3,
    "searchstring": 4,
    "datetime": 5,
    "regex": 6,
    "numeric": 7,
    "boolean": 8,
    "nulltype": 9,
    "json": 10,
    "string": 11
}


def validate(raw_recipe, sous_chef):
    """
    Given a raw recipe and it's associated sous chef,
    validate and parse the recipe.
    """
    uninitialized = raw_recipe.get('status') == 'uninitialized'
    rs = RecipeSchema(raw_recipe, sous_chef, uninitialized)
    return rs.validate()


def update(old_recipe, new_recipe, sous_chef):
    """
    Given a partial or completely new recipe, update the old recipe
    and re-validate it.
    """

    # if the old recipe is a Recipe object, coerce it to and from json.
    if isinstance(old_recipe, Recipe):
        old_recipe = json_to_obj(obj_to_json(old_recipe))

    # format it correctly first.
    _rs = RecipeSchema(new_recipe, sous_chef)
    _rs.format_recipe()
    new_recipe = copy.copy(_rs.recipe)

    # update the previous version.
    new_recipe = update_nested_dict(old_recipe, new_recipe, overwrite=True)

    # revalidate.
    rs = RecipeSchema(new_recipe, sous_chef)
    return rs.validate()


class RecipeSchema(object):

    """
    A class for aiding in recipe option parsing + validation.
    """

    def __init__(self, recipe, sous_chef, uninitialized=False):
        self.recipe = copy.deepcopy(recipe)
        if not 'options' in self.recipe:
            self.recipe['options'] = {}
        self.sous_chef = sous_chef.get('slug')
        self.sous_chef_name = sous_chef.get('name')
        self.sous_chef_desc = sous_chef.get('description')
        self.sous_chef_opts = sous_chef.get('options')
        self.uninitialized = uninitialized

    def get_opt(self, key, top_level=False):
        """
        Get a recipe opt and check for missingness.
        """
        sc_opt = self.sous_chef_opts.get(key)
        if top_level:
            opt = self.recipe.get(key, None)
        else:
            opt = self.recipe['options'].get(key, None)

        if opt is None:
            if sc_opt.get('required', False):

                # check for a default
                if 'default' in sc_opt:
                    return sc_opt.get('default')

                elif self.uninitialized:
                    return None

                msg = "Missing required option '{}".format(key)
                self._raise_recipe_schema_error(msg)

            else:
                return sc_opt.get('default', None)

        return opt

    def valid_nulltype(self, key, opt):
        """

        """
        if opt is None:
            return None
        else:
            try:
                if opt.lower() in NULL_VALUES:
                    return None
            except:
                pass
        return RecipeSchemaError(
            "{} should be a 'nulltype' field but was passed '{}'."
            .format(key, opt))

    def valid_crontab(self, key, opt):
        """
        Validate a crontab option.
        """
        if opt is None:
            return None
        try:
            dates.cron(opt)
        except Exception as e:
            return RecipeSchemaError(
                "{} should be a 'crontab' field but was passed '{}'. "
                "Here is the error message: {}."
                .format(key, opt, e.message))
        return opt

    def valid_datetime(self, key, opt):
        """
        Validate a iso-datetime option.
        """
        v_opt = dates.parse_iso(opt)
        if not v_opt:
            return RecipeSchemaError(
                "{} should be a 'datetime' field but was passed '{}'."
                .format(key, opt))
        return v_opt

    def valid_json(self, key, opt):
        """
        Validate a iso-datetime option.
        """
        try:
            obj_to_json(opt)
        except:
            return RecipeSchemaError(
                "{} should be a 'json' field but was passed '{}'."
                .format(key, opt))
        return opt

    def valid_searchstring(self, key, opt):
        """
        Validate a searchstring option.
        """
        try:
            return SearchString(opt)
        except SearchStringError as e:
            return RecipeSchemaError(
                "{} should be a 'searchstring' field but was passed '{}'. "
                "Here is the specific error: {}."
                .format(key, opt, e.message))

    def valid_boolean(self, key, opt):
        """
        Validate a boolean option.
        """
        try:
            opt = str(opt)
            if opt.lower() in TRUE_VALUES:
                return True
            if opt.lower() in FALSE_VALUES:
                return False
        except:
            return RecipeSchemaError(
                "{} is an 'boolean' field but was passed '{}'."
                .format(key, opt))

    def valid_numeric(self, key, opt):
        """
        Validate a numeric option.
        """
        try:
            return parse_number(opt)
        except:
            return RecipeSchemaError(
                "{} is an 'numeric' field but was passed '{}'."
                .format(key, opt))

    def valid_string(self, key, opt):
        """
        Validate a string field.
        """
        try:
            return unicode(opt)
        except:
            return RecipeSchemaError(
                "{} should be a 'string' field but was passed '{}'."
                .format(key, opt))

    def valid_url(self, key, opt):
        """
        Validate a url field.
        """
        if url.validate(opt):
            return opt
        return RecipeSchemaError(
            "{} should be a 'url' field but was passed '{}'."
            .format(key, opt))

    def valid_email(self, key, opt):
        """
        Validate a email field.
        """
        if mail.validate(opt):
            return opt
        return RecipeSchemaError(
            "{} can be an 'email' field but was passed '{}'."
            .format(key, opt))

    def valid_regex(self, key, opt):
        """
        Validate a email field.
        """
        try:
            return re.compile(opt)
        except:
            return RecipeSchemaError(
                "{} should be a 'regex' field but was passed '{}'."
                .format(key, opt))

    def validate_type(self, key, opt, type):
        """
        Validate any option type.
        """
        fx_lookup = {
            "string": self.valid_string,
            "numeric": self.valid_numeric,
            "crontab": self.valid_crontab,
            "json": self.valid_json,
            "email": self.valid_email,
            "url": self.valid_url,
            "regex": self.valid_regex,
            "boolean": self.valid_boolean,
            "datetime": self.valid_datetime,
            "nulltype": self.valid_nulltype,
            "searchstring": self.valid_searchstring
        }
        return fx_lookup.get(type)(key, opt)

    def validate_types(self, key, opt, types):
        """
        Validate an option that accepts 1 or more types.
        """
        error_messages = []

        # order types by proper check order
        types.sort(key=lambda val: TYPE_SORT_ORDER[val])

        # check types
        for type in types:
            ret = self.validate_type(key, opt, type)
            if isinstance(ret, RecipeSchemaError):
                error_messages.append(ret.args[0])
            else:
                return ret
        msg = "The following options are invalid: {}"\
              .format("\n\t- ".join(error_messages))
        self._raise_recipe_schema_error(msg)

    def validate_opt(self, key, top_level=False):
        """
        Validate any option.
        """
        sc_opt = self.sous_chef_opts.get(key)
        types = sc_opt.get('value_types')
        opt = self.get_opt(key, top_level=top_level)

        # opts that have been coerced to null here
        # should just be returned.
        if opt is None:
            return None

        # validate options which accept lists
        if isinstance(opt, list):
            if not sc_opt.get('accepts_list', False):
                msg = "{} does not accept lists.".format(key)
                self._raise_recipe_schema_error(msg)

            opts = []
            for o in opt:
                o = self.validate_types(key, o, types)
                opts.append(o)
            return opts

        # validate simple options
        return self.validate_types(key, opt, types)

    def format_recipe(self):
        """
        Make sure recipe items are in the right place.
        """
        # remove all internal fields.
        for key in RECIPE_REMOVE_FIELDS:
            self.recipe.pop(key, None)

        # make sure default options are not in `options`.
        for key in self.recipe['options'].keys():
            if key in SOUS_CHEF_DEFAULT_OPTIONS.keys():
                self.recipe[key] = self.recipe['options'].pop(key)

        # make sure recipe options are in `options`
        for key in self.recipe.keys():
            if key not in SOUS_CHEF_DEFAULT_OPTIONS.keys() and\
               key not in RECIPE_INTERNAL_FIELDS and\
               key != 'options':

                self.recipe['options'][key] = self.recipe.pop(key)

        # make sure no non-sc fields are in options
        for key in self.recipe['options'].keys():
            if key not in self.sous_chef_opts:
                self.recipe['options'].pop(key, None)

    def update_sous_chef_defaults(self):
        """
        Merge in sous chef defaults.
        """
        for key in SOUS_CHEF_DEFAULT_OPTIONS.keys():
            # if the key is in the recipe
            # validate it and add in back in.
            if key in self.recipe:
                self.recipe[key] = self.validate_opt(key, top_level=True)

            # otherwise, merge it in.
            else:
                # if the key should be a slug, fall back on the sous chef
                # slug and add a random hash.
                if key == 'slug':
                    slug = "{}-{}".format(self.sous_chef, gen_short_uuid())
                    self.recipe['slug'] = slug

                # inhert the sous chef's name + description
                elif key == 'name':
                    self.recipe[key] = self.sous_chef_name

                # inhert the sous chef's name + description
                elif key == 'description':
                    self.recipe[key] = self.sous_chef_desc

                # fallback on sous chef defaults.
                else:
                    self.recipe[key] = self.validate_opt(key, top_level=True)

    def validate_schedule(self):
        """
        Validate recipe schedule options.
        """
        # check that the associated schedule field is set.
        if not self.recipe.get('schedule_by', None):
            self.recipe['schedule_by'] = 'unscheduled'
        for typ in RECIPE_SCHEDULE_METHODS:
            if typ != 'unscheduled' and \
               self.recipe.get('schedule_by') == typ and \
               not self.recipe.get(typ, None):

                msg = "Recipe is set to be scheduled by '{}' "\
                      "but is missing an associated value."\
                      .format(typ)
                self._raise_recipe_schema_error(msg)

    def validate(self):
        """
        Validate a recipe.
        """
        # format it
        self.format_recipe()

        # merge in sous chef defaults.
        self.update_sous_chef_defaults()

        # validate and parse the options:
        for key in self.sous_chef_opts.keys():
            if key not in SOUS_CHEF_DEFAULT_OPTIONS.keys():
                self.recipe['options'][key] = self.validate_opt(key)

        # validate the schedule
        self.validate_schedule()

        # return the valid recipe
        return copy.copy(self.recipe)

    def _raise_recipe_schema_error(self, message):
        """
        A helper for raising consistent error messages.
        """
        r = self.recipe.get('slug', self.recipe.get('name', ''))
        preface = "There were problems validating Recipe '{}' "\
                  "which is associated with SousChef '{}' -- "\
                  .format(r, self.sous_chef)
        msg = preface + message
        raise RecipeSchemaError(msg)
