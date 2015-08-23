"""
Global defaults. These are non-configurable.
"""

# METRICS
METRIC_TYPES = [
    'count', 'cumulative', 'percentile',
    'median', 'average', 'min_rank',
    'max_rank', 'computed'
]

METRIC_AGGS = [
    'min', 'max', 'avg', 'sum', 'median'
]


METRIC_CONTENT_LEVELS = [
    'timeseries', 'summary', 'comparison'
]


METRIC_ORG_LEVELS = [
    'timeseries', 'summary'
]

METRIC_FACET_KEYS = [
    'facet', 'value'
]

METRIC_TS_UNITS = [
    'hour', 'day', 'month', None
]

CONTENT_METRIC_COMPARISONS = [
    'all', 'types', 'impact_tags', 'subject_tags'
]

# EVENTS
EVENT_STATUSES = [
    'approved', 'pending', 'deleted'
]

EVENT_TYPES = [
    'promotion', 'alert', 'manual'
]

EVENT_PROVENANCES = [
    'manual', 'recipe'
]

EVENT_FACETS = [
    'tags', 'content_items', 'levels',
    'categories', 'sous_chefs',
    'recipes', 'statuses', 'provenances',
    'domains'
]

EVENT_SEARCH_VECTORS = [
    'meta', 'body', 'title',
    'authors', 'description', 'all'
]


# CONTENT ITEMS
CONTENT_ITEM_TYPES = [
    'video', 'article',
    'slideshow', 'interactive',
    'podcast'
]

CONTENT_ITEM_EVENT_FACETS = [
    'events', 'categories',
    'levels', 'event_statuses'
]

CONTENT_ITEM_FACETS = [
    'subject_tags', 'provenances',
    'sous_chefs', 'recipes', 'impact_tags',
    'types', 'domains', 'authors',
    'site_names'
    ] + CONTENT_ITEM_EVENT_FACETS

CONTENT_ITEM_PROVENANCES = [
    'manual', 'recipe'
]

CONTENT_ITEM_SEARCH_VECTORS = [
    'meta', 'body', 'title',
    'authors', 'description', 'all'
]

# SOUS CHEFS
SOUS_CHEF_CREATES = [
    'events', 'content', 'tags',
    'metrics', 'series', 'report',
    'external', 'internal', 'null'
]

# RECIPES
RECIPE_STATUSES = [
    'queued',
    'running', 'error', 'stable',
    'uninitialized', 'inactive'
]

# fields which we will remove before validation
RECIPE_REMOVE_FIELDS = [
    'id', 'sous_chef_id', 'user_id', 'org_id',
    'created', 'updated', 'scheduled', 'sous_chef'
]

# field which will not validate but will passthrough.
RECIPE_INTERNAL_FIELDS = [
    'status', 'last_run', 'last_job'
]

RECIPE_SCHEDULE_TYPES = [
    'minutes', 'crontab', 'time_of_day',
    'unscheduled'
]

RECIPE_SCHEDULE_METHODS = [
    'minutes', 'crontab', 'time_of_day',
    'unscheduled'
]

SOUS_CHEF_RESERVED_FIELDS = RECIPE_REMOVE_FIELDS + RECIPE_INTERNAL_FIELDS

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

TASK_QUEUE_NAMES = [
    'recipe',
    'bulk'
]
TEMPLATE_FORMATS = [
    'html',
    'md'
]

# boolean parsing.
TRUE_VALUES = [
    'y', 'yes', '1', 't', 'true', 'on', 'ok'
]

FALSE_VALUES = [
    'n', 'no', '0', 'f', 'false', 'off'
]

NULL_VALUES = [
    'null', 'na', 'n/a', 'nan', 'none'
]
