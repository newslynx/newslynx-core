"""
Global defaults. These are non-configurable.
"""

# THINGS

## TK: refine these.
THING_TYPES = [
    'video', 'article', 'slideshow', 'interactive',
    'podcast'
]

# METRICS

METRIC_CATEGORIES = ['promotion', 'performance', 'impact']

# EVENTS

EVENT_STATUSES = ['approved', 'pending', 'deleted']

## TODO: move this out of here.
EVENT_FACETS = ['tags', 'things', 'levels', 'categories', 'sous_chefs', 'recipes', 'statuses']

# THINGS
THING_FACETS = ['tags', 'events', 'levels', 'categories', 'sous_chefs', 'recipes', 'types', 'domains']

# TAGS

TAG_TYPES = [
    'impact', 'subject'
]
IMPACT_TAG_CATEGORIES = [
    'citation', 'change', 'achievement', 'other'
]
IMPACT_TAG_LEVELS = [
    'instituion', 'media', 'community', 'individual', 'internal'
]
