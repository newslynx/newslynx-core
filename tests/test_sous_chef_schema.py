import unittest

from newslynx.exc import SousChefSchemaError
from newslynx.models import sous_chef_schema, SousChef
from newslynx.core import gen_session

db_session = gen_session()


class TestSousChefJSONSchema(unittest.TestCase):

    def test_good_schema(self):
        sc = {
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
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        sous_chef_schema.validate(sc)

    def test_good_metrics_schema(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter-list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "metrics",
            "metrics": {
                "ga_pageviews": {
                    "display_name": "Pageviews",
                    "type": "count",
                    "content_levels": ['timeseries', 'summary', 'comparison'],
                    "org_levels": [],
                    "faceted": False,
                    "agg": "sum"
                }
            },
            "options": {
                "age_of_article": {
                    "input_type": "number",
                    "value_types": ["numeric", "nulltype"],
                    "accepts_list": False,
                    "required": False,
                    "default": None,
                    "help": {
                        "description": "The age of content-items (in days) which metrics will be pulled for.",
                        "placeholder": "cspan"
                    }
                }
            }
        }
        sous_chef_schema.validate(sc)

    # def test_metrics_schema_missing_display_name(self):
    #     sc = {
    #         "name": "Google Analytics Content Timeseries",
    #         "slug": "twitter-list",
    #         "description": "Grabs timeseries metrics for content items from Google Analytics.",
    #         "runs": "newslynx.sc.events.twitter.List",
    #         "creates": "metrics",
    #         "metrics": {
    #             "ga_pageviews": {
    #                 "timeseries": True,
    #                 "cumulative": False,
    #                 "faceted": False,
    #                 "aggregation": "sum",
    #                 "level": "content_item"
    #             },
    #             "ga_entrances": {
    #                 "display_name": "Entrances",
    #                 "timeseries": True,
    #                 "cumulative": False,
    #                 "faceted": False,
    #                 "aggregation": "sum",
    #                 "level": "content_item"
    #             },
    #             "ga_exits": {
    #                 "display_name": "Entrances",
    #                 "timeseries": True,
    #                 "cumulative": False,
    #                 "faceted": False,
    #                 "aggregation": "sum",
    #                 "level": "content_item"
    #             }
    #         },
    #         "options": {
    #             "age_of_article": {
    #                 "input_type": "number",
    #                 "value_types": ["numeric", "nulltype"],
    #                 "accepts_list": False,
    #                 "required": False,
    #                 "default": None
    #             }
    #         }
    #     }
    #     try:
    #         sous_chef_schema.validate(sc)
    #     except SousChefSchemaError:
    #         assert True
    #     else:
    #         assert False

    # def test_metrics_schema_timeseries_faceted_error(self):
    #     sc = {
    #         "name": "Google Analytics Content Timeseries",
    #         "slug": "twitter-list",
    #         "description": "Grabs timeseries metrics for content items from Google Analytics.",
    #         "runs": "newslynx.sc.events.twitter.List",
    #         "creates": "metrics",
    #         "metrics": {
    #             "ga_pageviews": {
    #                 "display_name": "Pageviews",
    #                 "timeseries": True,
    #                 "cumulative": False,
    #                 "faceted": True,
    #                 "aggregation": "sum",
    #                 "level": "content_item"
    #             },
    #             "ga_entrances": {
    #                 "display_name": "Entrances",
    #                 "timeseries": True,
    #                 "cumulative": False,
    #                 "faceted": False,
    #                 "aggregation": "sum",
    #                 "level": "content_item"
    #             },
    #             "ga_exits": {
    #                 "display_name": "Entrances",
    #                 "timeseries": True,
    #                 "cumulative": False,
    #                 "faceted": False,
    #                 "aggregation": "sum",
    #                 "level": "content_item"
    #             },
    #         },
    #         "options": {
    #             "age_of_article": {
    #                 "input_type": "number",
    #                 "value_types": ["numeric", "nulltype"],
    #                 "accepts_list": False,
    #                 "required": False,
    #                 "default": None,
    #                 "help": {
    #                     "description": "The age of content-items (in days) which metrics will be pulled for.",
    #                     "placeholder": "cspan"
    #                 }
    #             }
    #         }
    #     }
    #     try:
    #         sous_chef_schema.validate(sc)
    #     except SousChefSchemaError:
    #         assert True
    #     else:
    #         assert False


    def test_metrics_schema_no_metrics(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter-list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "metrics",
            "options": {
                "age_of_article": {
                    "input_type": "number",
                    "value_types": ["numeric", "nulltype"],
                    "accepts_list": False,
                    "required": False,
                    "default": None,
                    "help": {
                        "description": "The age of content-items (in days) which metrics will be pulled for.",
                        "placeholder": "cspan"
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_bad_slug_format(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "text",
                    "value_types": ["text"],
                    "accepts_list": True,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_missing_options(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter-list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events"
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_checkbox_non_multiple_option(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "checkbox",
                    "value_types": ["text"],
                    "accepts_list": False,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_followers": {
                    "input_type": "number",
                    "value_types": ["number"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_datepicker_non_datetime(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "datepicker",
                    "value_types": ["string"],
                    "accepts_list": False,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_followers": {
                    "input_type": "number",
                    "value_types": ["number"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_number_non_numeric(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "number",
                    "value_types": ["string"],
                    "accepts_list": False,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_followers": {
                    "input_type": "number",
                    "value_types": ["number"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_paragraph_non_string(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "paragraph",
                    "value_types": ["numeric"],
                    "accepts_list": False,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_folowers": {
                    "input_type": "number",
                    "value_types": ["number"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_text_non_string(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "paragraph",
                    "value_types": ["numeric"],
                    "accepts_list": False,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_followers": {
                    "input_type": "number",
                    "value_types": ["number"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_searchstring_non_text(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "paragraph",
                    "value_types": ["searchstring"],
                    "accepts_list": False,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_folowers": {
                    "input_type": "number",
                    "value_types": ["number"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_url_non_text(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "paragraph",
                    "value_types": ["url"],
                    "accepts_list": False,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    }
                },
                "min_followers": {
                    "input_type": "number",
                    "value_types": ["number"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_email_non_text(self):
        sc = {
            "name": "Google Analytics Content Timeseries",
            "slug": "twitter_list",
            "description": "Grabs timeseries metrics for content items from Google Analytics.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "owner_screen_name": {
                    "input_type": "paragraph",
                    "value_types": ["email"],
                    "accepts_list": False,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    }
                },
                "min_followers": {
                    "input_type": "number",
                    "value_types": ["number"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_reserved_name(self):
        sc = {
            "name": "Twitter List",
            "slug": "twitter-list",
            "description": "Extracts events from a twitter list.",
            "runs": "newslynx.sc.events.twitter.List",
            "creates": "events",
            "options": {
                "user_id": {
                    "input_type": "text",
                    "value_types": ["string"],
                    "accepts_list": True,
                    "required": True,
                    "help": {
                        "placeholder": "cspan"
                    },
                },
                "min_folowers": {
                    "input_type": "number",
                    "value_types": ["numeric"],
                    "accepts_list": False,
                    "required": False,
                    "default": 0
                }
            }
        }
        try:
            sous_chef_schema.validate(sc)
        except SousChefSchemaError:
            assert True
        else:
            assert False

    def test_partial_update(self):
        """
        Simiulate a partial update process.
        """
        sc = {
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
                    "accepts_list": False,
                    "required": False,
                    "default": 0,
                    "help": {
                        "placeholder": 1000
                    }
                }
            }
        }
        sc = sous_chef_schema.validate(sc)
        sc = SousChef(**sc)
        db_session.add(sc)
        db_session.commit()

        new_sc = {
            'name': 'Twitter List to Event',
            'options': {
                'owner_screen_name': {
                    'accepts_list': False
                }
            }
        }
        new_sc = sous_chef_schema.update(sc, new_sc)
        assert(new_sc['name'] == 'Twitter List to Event')
        assert(new_sc['options']['owner_screen_name']['accepts_list'] is False)
        db_session.delete(sc)
        db_session.commit()

if __name__ == '__main__':
    unittest.main()
