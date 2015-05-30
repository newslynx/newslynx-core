from functools import wraps
import logging
import time

import requests

from newslynx import settings

log = logging.getLogger(__name__)


def get_request_kwargs(timeout, useragent):
    """This Wrapper method exists b/c some values in req_kwargs dict
    are methods which need to be called every time we make a request
    """
    return {
        'headers': {'User-Agent': useragent},
        'timeout': timeout,
        'allow_redirects': True
    }


def get_html(url, config=None, response=None):
    """Retrieves the html for either a url or a response object. All html
    extractions MUST come from this method due to some intricies in the
    requests module. To get the encoding, requests only uses the HTTP header
    encoding declaration requests.utils.get_encoding_from_headers() and reverts
    to ISO-8859-1 if it doesn't find one. This results in incorrect character
    encoding in a lot of cases.
    """
    FAIL_ENCODING = 'ISO-8859-1'
    useragent = settings.BROWSER_USER_AGENT
    timeout = settings.BROWSER_TIMEOUT

    if response is not None:
        if response.encoding != FAIL_ENCODING:
            return response.text
        return response.content

    try:
        html = None
        response = requests.get(
            url=url, **get_request_kwargs(timeout, useragent))
        if response.encoding != FAIL_ENCODING:
            html = response.text
        else:
            html = response.content
        if html is None:
            html = ''
        return html
    except Exception as e:
        log.debug('%s on %s' % (e, url))
        return ''


def retry(*dargs, **dkwargs):
    """A decorator for performing http requests and catching all concievable errors.
       Useful for including in scrapers for unreliable webservers.
       @retry(attempts=3)
       def buggy_request():
           return requests.get('http://www.gooooooooooooogle.com')
       buggy_request()
       >>> None
    """
    # set defaults
    attempts = dkwargs.get('attempts', settings.BROWSER_MAX_RETRIES)
    wait = dkwargs.get('wait', settings.BROWSER_WAIT)
    backoff = dkwargs.get('backoff', settings.BROWSER_BACKOFF)
    verbose = dkwargs.get('verbose', True)
    raise_uncaught_errors = dkwargs.get('raise_uncaught_errors', False)

    # wrapper
    def wrapper(f):

        # logger
        log = logging.getLogger(f.__name__)

        @wraps(f)
        def wrapped_func(*args, **kw):

            # defaults
            r = None
            tries = 0
            err = True

            # for ref problems
            bckof = backoff * 1
            wait_time = wait * 1

            while 1:

                # if we've exceeded the maximum number of tries,
                # return
                if tries == attempts:
                    if verbose:
                        log.error('Request Failed after {} tries.'.format(tries))
                    return r

                # increment tries
                tries += 1

                # calc wait time for this step
                wait_time *= bckof

                # try the function
                try:
                    r = f(*args, **kw)
                    err = False

                except Exception as e:
                    if verbose:
                        log.warning('Exception - {} on try {}'.format(e, tries))
                    if raise_uncaught_errors:
                        raise e
                    else:
                        time.sleep(wait_time)

                # check the status code if its a response object
                if isinstance(r, requests.Response):
                    try:
                        r.raise_for_status()
                    except requests.exceptions.HTTPError as e:
                        if verbose:
                            log.warning('Bad Status Code - {}'.format(r.status_code))
                        time.sleep(wait_time)

                elif not err:
                    break

                return r

            return wrapped_func

        return wrapper
