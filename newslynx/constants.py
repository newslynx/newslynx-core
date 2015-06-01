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
    'tags', 'things', 'levels',
    'categories', 'sous_chefs',
    'recipes', 'statuses', 'provenances'
]


# THINGS

# TK: refine these.
THING_TYPES = [
    'video', 'article', 'slideshow',
    'interactive', 'podcast'
]

THING_EVENT_FACETS = [
    'events', 'categories', 'levels',
    'event_statuses'
]

THING_FACETS = [
    'tags', 'provenances',
    'sous_chefs', 'recipes',
    'types', 'domains'
    ] + THING_EVENT_FACETS

THING_PROVENANCES = ['manual', 'recipe']

# SOUS CHEFS

SOUS_CHEF_CREATES = [
    'event', 'thing', 'tag',
    'metric', 'series', 'report'
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
