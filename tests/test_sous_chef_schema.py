import unittest

from newslynx.models import SOUS_CHEF_JSON_SCHEMA
from newslynx.lib.serialize import json_to_obj
from jsonschema import Draft4Validator

# setup validator
validator = Draft4Validator(SOUS_CHEF_JSON_SCHEMA)


def validate_sous_chef_schema(schema):
    return sorted(validator.iter_errors(schema), key=lambda e: e.path)


class TestSousChefJSONSchema(unittest.TestCase):

    def test_good_schema(self):
        print 'A valid sous chef schema has a name, descritpion, rungs, creates, and options fields.'
        example = {
            "name": "Twitter List",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.TwitterList",
            "creates": "thing",
            "options": {
                "requires_approval": {
                    "type": "boolean",
                    "default": True,
                    "required": False
                },
                "name": {
                    "type": "text",
                    "required": True,
                    "help": {
                        "placeholder": "Empire funding discussion",
                        "link": "http://twitter.com/what-is-a-list-or-something"
                    }
                },
                "owner_screen_name": {
                    "type": "text",
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_folowers": {
                    "type": "number",
                    "help": {
                        "placeholder": "Show from people with X followers, e.g. 5000",
                    }
                }
            }
        }
        errors = validate_sous_chef_schema(example)
        if len(errors):
            for e in errors:
                print e.message, e.path
            raise

    def test_missing_type(self):
        print 'All sous chef schema options should have types.'
        example = {
            "name": "Twitter List",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.TwitterList",
            "creates": "thing",
            "options": {
                "requires_approval": {
                    "default": True,
                    "required": False
                },
                "name": {
                    "type": "text",
                    "required": True,
                    "help": {
                        "placeholder": "Empire funding discussion",
                        "link": "http://twitter.com/what-is-a-list-or-something"
                    }
                },
                "owner_screen_name": {
                    "type": "text",
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_folowers": {
                    "type": "number",
                    "help": {
                        "placeholder": "Show from people with X followers, e.g. 5000",
                    }
                }
            }
        }
        errors = validate_sous_chef_schema(example)
        assert len(errors)
        for e in errors:
            assert "type" in e.message

    def test_missing_help_placeholder(self):
        print 'If a sous-chef option has a help field, it needs a placeholder.'
        example = {
            "name": "Twitter List",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.TwitterList",
            "creates": "thing",
            "options": {
                "requires_approval": {
                    "type": "boolean",
                    "default": True,
                    "required": False
                },
                "name": {
                    "type": "text",
                    "required": True,
                    "help": {
                        "placeholder": "Empire funding discussion",
                        "link": "http://twitter.com/what-is-a-list-or-something"
                    }
                },
                "owner_screen_name": {
                    "type": "text",
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_folowers": {
                    "type": "number",
                    "help": {
                    }
                }
            }
        }
        errors = validate_sous_chef_schema(example)
        assert len(errors)
        for e in errors:
            print e.message
            assert "placeholder" in e.message

    def test_bad_option_type(self):
        print 'If a sous-chef option has a help field, it needs a placeholder.'
        example = {
            "name": "Twitter List",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.TwitterList",
            "creates": "thing",
            "options": {
                "requires_approval": {
                    "type": "bad-option",
                    "default": True,
                    "required": False
                },
                "name": {
                    "type": "text",
                    "required": True,
                    "help": {
                        "placeholder": "Empire funding discussion",
                        "link": "http://twitter.com/what-is-a-list-or-something"
                    }
                },
                "owner_screen_name": {
                    "type": "text",
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_folowers": {
                    "type": "number",
                    "help": {
                        "placeholder": "yo"
                    }
                }
            }
        }
        errors = validate_sous_chef_schema(example)
        assert len(errors)
        for e in errors:
            print e.message
            assert "bad-option" in e.message