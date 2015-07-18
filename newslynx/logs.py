"""
Logging Configurations and some custom logging classes.
"""
import logging
import sys
from traceback import format_exc
from datetime import datetime 

from colorama import Fore

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

oauth2client_client_log = logging.getLogger('oauth2client')
oauth2client_client_log.setLevel(logging.ERROR)

googleapiclient = logging.getLogger('googleapiclient')
googleapiclient.setLevel(logging.ERROR)


def color(c):
    c = getattr(Fore, c.upper(), None)
    if not c:
        c = Fore.WHITE
    return c


class ColorLog(object):
    """
    A colored logger.
    """
    def __init__(self, **kw):
        self.date_format = kw.get('date_format', '%H:%M:%S')
        self._now = kw.get('now', datetime.now)

    @property
    def now(self):
        return self._now().strftime(self.date_format)

    def colorize(self, msg, **kw):
        if kw.get('color', None):
            c = color(kw['color'])
            msg = '{0}{1}{2}'.format(c, msg, Fore.RESET)
        return msg

    def format(self, msg, **kw):
        msg = self.colorize(msg, **kw)
        if kw.get('line', True):
            msg = "{} | {}\n".format(self.colorize(self.now, color='blue'), msg)
        return msg

    def stdout(self, msg, **kw):
        sys.stdout.write(self.format(msg, **kw))

    def stderr(self, msg, **kw):
        sys.stderr.write(self.format(msg, **kw))

    def info(self, msg, **kw):
        kw.setdefault('color', 'green')
        self.stderr(msg, **kw)

    def warning(self, msg, **kw):
        kw.setdefault('color', 'yellow')
        self.stderr(msg, **kw)

    def error(self, msg, **kw):
        kw.setdefault('color', 'red')
        self.stderr(msg, **kw)

    def exception(self, e, **kw):
        kw.setdefault('tb', True)
        self.error('{} : {}'.format(e.__class__.__name__, e.message),  **kw)
        if kw['tb']:
            tb = format_exc()
            self.warning(tb, **kw)


class StdLog(ColorLog):
    """
    A standard logger.
    """
    def colorize(self, msg, **kw):
        return msg
