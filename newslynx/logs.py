"""
Logging Configurations and some custom logging classes.
"""
import logging

from colorlog import ColoredFormatter


from newslynx.lib.serialize import obj_to_json
from newslynx import settings

# a lookup of levelname => object
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# a lookup of level => color
LOG_COLORS = {
    'DEBUG':    'cyan',
    'INFO':     'green',
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'red',
}

# setup core logger
LOGGERS = {
    'COLOR': "%(blue)s%(asctime)s%(reset)s | %(white)s%(name)s%(reset)s-%(white)s%(lineno)s%(reset)s | %(message_log_color)s%(message)s%(reset)s",
    'STD': "%(asctime)s | %(levelname)s | %(name)s-%(lineno)s | %(message)s"
}


class JSONLogger(logging.Formatter):

    """
    Log messages as JSON.
    """

    def format(self, record):
        """
        Return logging information as JSON.
        """
        fields = record.__dict__.copy()
        for k in fields.keys():
            if k not in settings.LOG_JSON_FIELDS:
                fields.pop(k, None)
        return obj_to_json(fields)


def setup_logger(**kw):
    """
    Setup root logger.
    """
    add_handler = kw.get('add_handler', False)
    try:
        from newslynx.core import settings
        level = kw.pop('level', settings.LOG_LEVEL)
        type = kw.pop('type', settings.LOG_TYPE)
        datefmt = kw.pop('datefmt', settings.LOG_DATE_FORMAT)
    except:
        level = 'info'
        type = 'color'
        datefmt = '%H:%M:%S'

    # create a new log stream handler, and configure it
    ch = logging.StreamHandler()

    if type.upper() == "COLOR":
        formatter = ColoredFormatter(
            LOGGERS['COLOR'],
            datefmt=datefmt,
            reset=True,
            log_colors=LOG_COLORS,
            secondary_log_colors={
                'message': LOG_COLORS
            }
        )
    elif type.upper() == 'JSON':
        formatter = JSONLogger()

    else:
        # create a default formatter
        formatter = logging.Formatter(LOGGERS['STD'], datefmt=datefmt)

    # install the formatter and add the handler to the root logger
    ch.setFormatter(formatter)
    logging.root.addHandler(ch)
    logging.root.setLevel(LOG_LEVELS[level.upper()])

    # suppress various loggers
    _suppress()


def _suppress():
    """
    Loggers to suppress
    """
    tld_log = logging.getLogger('tldextract')
    tld_log.setLevel(logging.CRITICAL)

    # shut up useless SA warning:
    import warnings
    warnings.filterwarnings('ignore',
                            'Unicode type received non-unicode bind param value.')
    from sqlalchemy.exc import SAWarning
    warnings.filterwarnings('ignore', category=SAWarning)
    warnings.filterwarnings('ignore', category=SAWarning)

    # specific loggers
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.ERROR)

    urllib3_log = logging.getLogger("urllib3")
    urllib3_log.setLevel(logging.ERROR)
    iso8601_log = logging.getLogger("iso8601")
    iso8601_log.setLevel(logging.ERROR)

    oauth2client_client_log = logging.getLogger('oauth2client')
    oauth2client_client_log.setLevel(logging.ERROR)

    googleapiclient = logging.getLogger('googleapiclient')
    googleapiclient.setLevel(logging.ERROR)

    import requests
    from requests.packages.urllib3.exceptions import (
        InsecureRequestWarning, InsecurePlatformWarning)
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
    warnings.filterwarnings('ignore', category=InsecureRequestWarning)
    warnings.filterwarnings('ignore', category=InsecurePlatformWarning)

