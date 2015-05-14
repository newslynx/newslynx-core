import unittest

from newslynx.exc import SousChefSchemaError
from newslynx.models import validate_sous_chef


class TestSousChefJSONSchema(unittest.TestCase):

    def test_good_schema(self):
        print 'A valid sous chef schema has a name, slug, descritpion, runs, creates, and options fields.'
        example = {
            "name": "Twitter List",
            "slug": "twitter-list",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "thing",
            "options": {
                "requires_approval": {
                    "type": "boolean",
                    "default": True,
                    "required": False
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
        try:
            validate_sous_chef(example)
        except SousChefSchemaError:
            assert False
        else:
            assert True

    def test_missing_type(self):
        print 'All sous chef schema options should have types.'
        example = {
            "name": "Twitter List",
            "slug": "twitter-list",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.events.twitter.List",
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
        try:
            validate_sous_chef(example)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_missing_help_placeholder(self):
        print 'If a sous-chef option has a help field, it needs a placeholder.'
        example = {
            "name": "Twitter List",
            "slug": "twitter-list",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.events.twitter.List",
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
        try:
            validate_sous_chef(example)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_bad_option_type(self):
        print 'If a sous-chef option has a help field, it needs a placeholder.'
        example = {
            "name": "Twitter List",
            "slug": "twitter-list",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.events.twitter.List",
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
        try:
            validate_sous_chef(example)
        except SousChefSchemaError:
            assert True
        else:
            assert False

if __name__ == '__main__':
    unittest.main()