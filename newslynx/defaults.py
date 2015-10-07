"""
Default configurations that can be overriden by
~/.newslynx/config.yaml or ENV variables.
"""

import os
from newslynx.util import here

_DEFAULT_CONFIG = here(__file__, "app/config.yaml")
_CONFIG_REQUIRES = [
    'super_user',
    'super_user_email',
    'super_user_apikey',
    'super_user_password',
    'sqlalchemy_database_uri',
    'secret_key'
]
_DEFAULT_DEFAULTS = here(__file__, "app/defaults/")

TESTING = False
CONFIG_FILE = os.getenv('NEWSLYNX_CONFIG_FILE',
                        os.path.expanduser('~/.newslynx/config.yaml'))

DEFAULT_TAGS = os.path.expanduser('~/.newslynx/defaults/tags.yaml')
DEFAULT_RECIPES = os.path.expanduser('~/.newslynx/defaults/recipes.yaml')

# sous chefs
SOUS_CHEFS_DIR = os.path.expanduser('~/.newslynx/sous-chefs/')

# app configurations #
API_URL = "http://localhost:5000"
API_DNS = "http://changeme.com:5000"
API_PORT = 5000
API_VERSION = "v1"

# logging configuration
LOG_TIMING = False
LOG_LEVEL = "info"
LOG_TYPE = 'color'
LOG_DATE_FORMAT = '%H:%M:%S'
LOG_JSON_FIELDS = [
    'name',
    'msg',
    'lineno',
    'created',
    'pathname',
    'levelname'
]

# security
SUPER_USER_ORG = 'admin'
SUPER_USER_ORG_TIMEZONE = 'UTC'

# DATABASE CONFIG
SQLALCHEMY_POOL_SIZE = 1000
SQLALCHEMY_POOL_MAX_OVERFLOW = 100
SQLALCHEMY_POOL_TIMEOUT = 60
SQLALCHEMY_ECHO = False

# TASK QUEUE
REDIS_URL = "redis://localhost:6379/0"

# URL CACHE
URL_CACHE_PREFIX = "newslynx-url-cache"
URL_CACHE_TTL = 1209600  # 14 DAYS
URL_CACHE_POOL_SIZE = 5

# EXTRACTION CACHE
EXTRACT_CACHE_PREFIX = "newslynx-extract-cache"
EXTRACT_CACHE_TTL = 259200  # 3 DAYS

# THUMBNAIL SETTINGS
THUMBNAIL_CACHE_PREFIX = "newslynx-thumbnail-cache"
THUMBNAIL_CACHE_TTL = 1209600  # 14 DAYS
THUMBNAIL_SIZE = [150, 150]
THUMBNAIL_DEFAULT_FORMAT = "PNG"

# COMPARISON CACHE
COMPARISON_CACHE_PREFIX = "newslynx-comparison-cache"
COMPARISON_CACHE_TTL = 86400  # 1 day
COMPARISON_PERCENTILES = [
    2.5, 5.0, 10.0, 20.0, 30.0,
    40.0, 60.0, 70.0, 80.0, 90.0,
    95.0, 97.5
]

# TODO, make this actually modify data.
COMPARISON_FUNCTIONS = ['min', 'max', 'avg', 'median']

# MERLYNNE KWARGS PREFIX
MERLYNNE_KWARGS_PREFIX = "newslynx-merlynne-kwargs"
MERLYNNE_KWARGS_TTL = 60
MERLYNNE_RESULTS_TTL = 60

# Scheduler
SCHEDULER_REFRESH_INTERVAL = 45
SCHEDULER_RESET_PAUSE_RANGE = [20, 200]

# browser
NETWORK_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0"
NETWORK_TIMEOUT = (7, 27)
NETWORK_WAIT = 0.8
NETWORK_BACKOFF = 2
NETWORK_MAX_RETRIES = 2

# reddit
REDDIT_USER_AGENT = 'Newslynx'

# Metrics timeseries granularity
METRICS_MIN_DATE_UNIT = 'hour'
METRICS_MIN_DATE_VALUE = 1
METRICS_CONTENT_LIST_TIMESERIES_DAYS = 5
METRICS_CONTENT_GET_TIMESERIES_DAYS = 30

# pandoc
PANDOC_PATH = '/usr/local/bin/pandoc'

# Notifications
NOTIFY_METHODS = []
NOTIFY_EMAIL_RECIPIENTS = []
NOTIFY_EMAIL_SUBJECT_PREFIX = "[ MERLYNNE ]"
NOTIFY_SLACK_WEBHOOK = None
NOTIFY_SLACK_CHANNEL = "#general"
NOTIFY_SLACK_USERNAME = "Merlynne"
NOTIFY_SLACK_EMOJI = ":-1:"

# Email
MAIL_USERNAME = ""
MAIL_PASSWORD = ""
MAIL_SERVER = ""
MAIL_SMTP_PORT = 587
MAIL_IMAP_PORT = 993
