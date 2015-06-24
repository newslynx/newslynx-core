"""
Logging Configurations
"""
import logging

## TODO CONFIGURE LOGGING PROPERLY
log = logging.getLogger('newslynx')

# suppress tld logging
tld_log = logging.getLogger('tldextract')
tld_log.setLevel(logging.CRITICAL)

# shut up useless SA warning:
import warnings
warnings.filterwarnings('ignore',
                        'Unicode type received non-unicode bind param value.')
from sqlalchemy.exc import SAWarning
warnings.filterwarnings('ignore', category=SAWarning)

# specific loggers
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.ERROR)

urllib3_log = logging.getLogger("urllib3")
urllib3_log.setLevel(logging.ERROR)
iso8601_log = logging.getLogger("iso8601")
iso8601_log.setLevel(logging.ERROR)
