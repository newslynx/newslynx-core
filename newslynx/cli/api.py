"""
Full access to the API client.
"""

import os
import sys
from inspect import isgenerator
import logging
from traceback import format_exc

log = logging.getLogger(__name__)

# build up collections and command tree.
_ignore_attrs = ['apikey', 'org', 'login', 'raise_errors']


def _keep(m):
    return not m.startswith('_') and m not in _ignore_attrs


def setup(parser):

    # dynamically list collections
    from newslynx.client import API
    api = API()
    collections = [c.replace('_', "-") for c in dir(api) if _keep(c)]

    api_parser = parser.add_parser("api", help="Access API methods.")
    api_parser.add_argument('collection', type=str, help='The API collection to access.',
                            choices=collections)
    api_parser.add_argument('method', type=str, default=None,
                            help='The method for the collection. Use "ls" to list all methods for a given collection.')
    api_parser.add_argument("-d", "--data", dest="data",
                            help="a .json / .yaml file, or a json string of the request's body")
    api_parser.add_argument("-e", "--raise-errors", action='store_true',
                            default=False,
                            help="Raise Errors as statements. If missing, will return JSON.")
    api_parser.add_argument('-u', '--apiurl', type=str,
                            default=os.getenv('NEWSLYNX_API_URL'),
                            help="The base url of Newslynx's API. Will default to $NEWSLYNX_API_URL")
    api_parser.add_argument('-k', '--apikey', dest="apikey", type=str,
                            default=os.getenv('NEWSLYNX_APIKEY'),
                            help="Your API key. Will default to $NEWSLYNX_APIKEY")
    api_parser.add_argument('-o', '--org', dest="org", type=str,
                            help="The ID/Slug of the organization you'd like to access. "
                            "Will default to $NEWSLYNX_ORG",
                            default=os.getenv('NEWSLYNX_ORG'))

    return 'api', run


def run(opts, **kwargs):

    from newslynx.lib import serialize
    from newslynx.cli.common import load_data

    # dynamically list collections
    from newslynx.client import API

    # connect to the api
    api = API(
        apikey=opts.apikey,
        org=opts.org,
        api_url=opts.apiurl,
        raise_errors=opts.raise_errors)

    # get the collection
    cobj = None
    if opts.collection:
        cobj = getattr(api, opts.collection.replace('-', '_'), None)
    if not cobj:
        # report options
        collections = [c.replace('_', "-") for c in dir(api) if _keep(c)]
        log.error("Collection '{}' does not exist."
                         .format(opts.collection))
        log.warning("Choose from the following collections:\n\t- {}"
                    .format(opts.collection, "\n\t- {}".join(collections)))
        sys.exit(1)

    # get the method
    mobj = None
    if opts.method:
        mobj = getattr(cobj, opts.method.replace('-', '_'), None)
    if not mobj:

        # report options
        if opts.method != 'ls':
            log.warning("Method '{}' does not exist for collection '{}'"
                        .format(opts.method, opts.collection))

        # compute the tree here to save on processing time.
        options = [m.replace('_', '-') for m in dir(cobj) if _keep(m)]

        # list of methods for this collection
        msg = "choose from the following methods:\n\t- {}"\
            .format("\n\t- ".join(options))

        log.warning("\n/{}\n".format(opts.collection) + msg)
        sys.exit(0)

    # parse body file / json string.
    d = load_data(opts.data)
    if d:
        kwargs.update(d)

    # execute method
    try:
        res = mobj(**kwargs)

    except KeyboardInterrupt as e:
        log.warning("\nInterrupted by user. Exiting...\n")
        sys.exit(2)  # interrupt

    except Exception as e:
        log.error(format_exc())
        sys.exit(1)

    # stream output
    if isgenerator(res):
        for r in res:
            sys.stdout.write(serialize.obj_to_json(r) + "\n")
    # stream
    else:
        sys.stdout.write(serialize.obj_to_json(res))
        sys.stdout.write("\n")
    sys.exit(0)
