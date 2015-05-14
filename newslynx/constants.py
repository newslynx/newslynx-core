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

EVENT_FACETS = [
    'tags', 'things', 'levels',
    'categories', 'sous_chefs',
    'recipes', 'statuses'
]


# THINGS

# TK: refine these.
THING_TYPES = [
    'video', 'article', 'slideshow',
    'interactive', 'podcast'
]

THING_FACETS = [
    'tags', 'events', 'levels',
    'categories', 'sous_chefs',
    'recipes', 'types', 'domains']


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
    'instituion', 'media',
    'community', 'individual', 'internal'
]
