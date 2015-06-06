import logging

from newslynx import settings

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

log = logging.getLogger(__name__)
log.addHandler(logging.basicConfig(
    format='%(levelname)s - %(asctime)s (%(name)s) %(message)s',
    level=LOG_LEVELS[getattr(settings, 'LOG_LEVEL', 'INFO').upper()],
    datefmt='%Y-%m-%d %H:%M:%S'
    ))

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
