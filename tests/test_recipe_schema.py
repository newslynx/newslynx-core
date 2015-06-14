import unittest
import datetime
import copy

import pytz

from newslynx.lib.search import SearchString
from newslynx.lib.serialize import obj_to_json
from newslynx.lib.regex import RE_TYPE
from newslynx.models import sous_chef_schema
from newslynx.models import recipe_schema
from newslynx.exc import RecipeSchemaError
from newslynx.models import Recipe, SousChef
from newslynx.core import db_session


sous_chef = {
    "name": "Twitter List",
    "slug": "twitter-list",
    "description": "Extracts events from a twitter list.",
    "runs": "newslynx.sc.events.twitter.List",
    "creates": "events",
    "options": {
        "owner_screen_name": {
            "input_type": "text",
            "value_types": ["string"],
            "accepts_list": True,
            "required": True,
            "help": {
                "placeholder": "cspan"
            },
        },
        "min_followers": {
            "input_type": "number",
            "value_types": ["numeric"],
            "required": True,
            "default": 0,
            "help": {
                "placeholder": 1000
            }
        },
        "start_date": {
            "input_type": "datepicker",
            "value_types": ["datetime", "nulltype"],
            "required": False,
            "default": None,
            "help": {
                "placeholder": '2015-05-06'
            }
        },
        "search_query": {
            "input_type": "text",
            "value_types": ["searchstring"],
            "required": False,
            "default": None,
            "help": {
                "placeholder": '~fracking | drilling'
            }
        },
        "tag_ids": {
            "input_type": "checkbox",
            "value_types": ["numeric", "string"],
            "accepts_list": True,
            "required": False,
            "default": []
        },
        "filter_bots": {
            "input_type": "select",
            "value_types": ["boolean"],
            "required": False,
            "default": "false"
        },
        "notify_email": {
            "input_type": "text",
            "value_types": ["email"],
            "required": False,
            "default": None
        },
        "link_url": {
            "input_type": "text",
            "value_types": ["url"],
            "required": False,
            "default": None
        },
        "user_regex": {
            "input_type": "text",
            "value_types": ["regex", "nulltype"],
            "required": False
        }
    }
}

sous_chef = sous_chef_schema.validate(sous_chef)

good_recipe = {
    "name": "My Cool Twitter List Recipe",
    "user_id": 1,
    "last_job": {},
    "owner_screen_name": ["foobar", "uqbar"],
    "description": "This is what my cool twitter list recipe does.",
    "time_of_day": "9:30 AM",
    "start_date": "2015-07-08",
    "interval": "null",
    "search_query": "~fracking | drilling",
    "user_regex": r".*",
    "link_url": "http://example.com/some-url",
    "notify_email": "brianabelson@gmail.com",
    "tag_ids": [1, 'this-is-also-a-tag'],
    "filter_bots": "t",
    "options": {}
}

good_recipe_proper_nesting = {
    "name": "My Cool Twitter List Recipe",
    "description": "This is what my cool twitter list recipe does.",
    "start_date": "2015-07-08",
    "time_of_day": "9:30 AM",
    "options": {
        "owner_screen_name": "foobar",
        "interval": "null",
        "user_regex": r".*",
        "link_url": "http://example.com/some-url",
        "notify_email": "brianabelson@gmail.com",
        "tag_ids": [1, 'this-is-also-a-tag'],
        "filter_bots": "t"
    }
}


class TestRecipeSchema(unittest.TestCase):

    def test_good_recipe_no_nesting(self):
        grecipe = copy.deepcopy(good_recipe)
        r = recipe_schema.validate(grecipe, sous_chef)
        o = r.get('options', {})

        # make sure name, slug, description, time of day, and interval are
        # extracted added to the top-level of recipe.
        assert('slug' in r)
        assert('description' in r)
        assert('name' in r)
        assert('time_of_day' in r)
        assert('interval' in r)

        # make sure scheduled determination has been made.
        assert('scheduled' in r)
        assert(r['scheduled'])

        # make sure user_id is not in recipe or options
        assert('user_id' not in r)
        assert('user_id' not in o)

        # make sure slug gets a new hash
        assert(sous_chef['slug'] != r['slug'])

        # make sure interval was parsed to null properly
        assert(r['interval'] is None)

        # make sure regex is parsed.
        assert(isinstance(o['user_regex'], RE_TYPE))

        # make sure start date is parsed
        assert(isinstance(o['start_date'], datetime.datetime))

        # make boolean is parsed
        assert(o['filter_bots'] is True)

        # make sure start date is UTC
        assert(o['start_date'].tzinfo == pytz.utc)

        # make sure min followers got filled in with it's defaults.
        assert(o['min_followers'] == 0)

        # assert screen name is list
        assert(isinstance(o['owner_screen_name'], list))

        # make sure search query is a SearchString
        assert(isinstance(o['search_query'], SearchString))

        # make sure we can serialize this back to json.
        obj_to_json(r)

    def test_good_recipe_nesting(self):
        r = recipe_schema.validate(good_recipe_proper_nesting, sous_chef)
        o = r.get('options', {})

        # make sure name, slug, description, time of day, and interval are
        # extracted added to the top-level of recipe.
        assert('slug' in r)
        assert('description' in r)
        assert('name' in r)
        assert('time_of_day' in r)
        assert('interval' in r)

        # make sure scheduled determination has been made.
        assert('scheduled' in r)
        assert(r['scheduled'])

        # make sure user_id is not in recipe or options
        assert('user_id' not in r)
        assert('user_id' not in o)

        # make sure slug gets a new hash
        assert(sous_chef['slug'] != r['slug'])

        # make sure interval was parsed to null properly
        assert(r['interval'] is None)

        # make sure regex is parsed.
        assert(isinstance(o['user_regex'], RE_TYPE))

        # make sure start date is parsed
        assert(isinstance(o['start_date'], datetime.datetime))

        # make boolean is parsed
        assert(o['filter_bots'] is True)

        # make sure start date is UTC
        assert(o['start_date'].tzinfo == pytz.utc)

        # make sure min followers got filled in with it's defaults.
        assert(o['min_followers'] == 0)

        # assert screen name is list
        assert(not isinstance(o['owner_screen_name'], list))

        # make sure search query is a SearchString
        assert(o['search_query'] is None)

        # make sure we can serialize this back to json.
        obj_to_json(r)

    def test_bad_date(self):
        grecipe = copy.copy(good_recipe)
        grecipe['start_date'] = '014u30214'
        try:
            recipe_schema.validate(grecipe, sous_chef)
            assert False
        except RecipeSchemaError:
            assert True

    def test_bad_numeric(self):
        grecipe = copy.copy(good_recipe)
        grecipe['interval'] = '014u30214'
        try:
            recipe_schema.validate(grecipe, sous_chef)
            assert False
        except RecipeSchemaError:
            assert True

    def test_bad_regex(self):
        grecipe = copy.copy(good_recipe)
        grecipe['user_regex'] = '014.****30214'
        try:
            recipe_schema.validate(grecipe, sous_chef)
            assert False
        except RecipeSchemaError:
            assert True

    def test_bad_search_query(self):
        grecipe = copy.copy(good_recipe)
        grecipe['search_query'] = '014u30214 OR asdfasasdf AND flakfsdlakfas'
        try:
            recipe_schema.validate(grecipe, sous_chef)
            assert False
        except RecipeSchemaError:
            assert True

    def test_bad_url(self):
        grecipe = copy.copy(good_recipe)
        grecipe['link_url'] = '014u30214 OR asdfasasdf AND flakfsdlakfas'
        try:
            recipe_schema.validate(grecipe, sous_chef)
            assert False
        except RecipeSchemaError:
            assert True

    def test_bad_email(self):
        grecipe = copy.copy(good_recipe)
        grecipe['notify_email'] = '014u30214 OR asdfasasdf AND flakfsdlakfas'
        try:
            recipe_schema.validate(grecipe, sous_chef)
            assert False
        except RecipeSchemaError:
            assert True

    def test_missing_required(self):
        grecipe = copy.copy(good_recipe)
        grecipe.pop('owner_screen_name')
        try:
            recipe_schema.validate(grecipe, sous_chef)
            assert False
        except RecipeSchemaError:
            assert True

    def test_partial_update(self):
        """
        Simiulate a partial update process.
        """
        old_recipe = copy.copy(good_recipe)

        sc = SousChef(**sous_chef)
        db_session.add(sc)
        db_session.commit()

        old_recipe = recipe_schema.validate(old_recipe, sc.to_dict())
        r = Recipe(sc, **old_recipe)
        db_session.add(r)
        db_session.commit()
        new_recipe = {
            'owner_screen_name': 'johnoliver',
            'last_job': {'foo': 'bar'},
            'status': 'stable'
        }
        new_recipe = recipe_schema.update(
            r, new_recipe, sc.to_dict())
        assert(new_recipe['options']['owner_screen_name'] == 'johnoliver')
        assert(new_recipe['last_job']['foo'] == 'bar')
        assert(new_recipe['status'] == 'stable')
        db_session.delete(r)
        db_session.delete(sc)
        db_session.commit()


if __name__ == '__main__':
    unittest.main()
