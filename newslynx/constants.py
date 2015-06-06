"""
Global defaults. These are non-configurable.
"""

# METRICS

METRIC_CATEGORIES = [
    'promotion', 'performance', 'impact'
]

# EVENTS

EVENT_STATUSES = [
    'approved', 'pending', 'deleted'
]

EVENT_TYPES = [
    'promotion', 'alert', 'manual'
]

EVENT_PROVENANCES = ['manual', 'recipe']

EVENT_FACETS = [
    'tags', 'content_items', 'levels',
    'categories', 'sous_chefs',
    'recipes', 'statuses', 'provenances'
]


# THINGS

# TK: refine these.
CONTENT_ITEM_TYPES = [
    'video', 'article', 'slideshow',
    'interactive', 'podcast'
]

CONTENT_ITEM_EVENT_FACETS = [
    'events', 'categories', 'levels',
    'event_statuses'
]

CONTENT_ITEM_FACETS = [
    'tags', 'provenances',
    'sous_chefs', 'recipes',
    'types', 'domains'
    ] + CONTENT_ITEM_EVENT_FACETS

CONTENT_ITEM_PROVENANCES = ['manual', 'recipe']

# SOUS CHEFS

SOUS_CHEF_CREATES = [
    'events', 'content', 'tags',
    'metrics', 'series', 'reports'
]

# RECIPES
RECIPE_STATUSES = [
    'running', 'error', 'stable', 'uninitialized'
]

# TAGS

TAG_TYPES = [
    'impact', 'subject'
]

IMPACT_TAG_CATEGORIES = [
    'promotion', 'citation', 'change',
    'achievement', 'other'
]

IMPACT_TAG_LEVELS = [
    'institution', 'media',
    'community', 'individual', 'internal'
]

# Views

THING_TIMESERIES_MAT_VIEW = 'thing_timeseries'
ORG_TIMESERIES_MAT_VIEW = 'org_timeseries'
