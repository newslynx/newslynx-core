import logging

logging.basicConfig(level=logging.INFO)

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
requests_log.setLevel(logging.WARNING)

urllib3_log = logging.getLogger("urllib3")
