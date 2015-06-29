import sys
import os
from inspect import isgenerator
from traceback import format_exc

from colorama import Fore
import argparse

from newslynx.cli.common import echo, echo_error, load_data
from newslynx.client import API
from newslynx.lib import serialize

# build up collections and command tree.
_ignore_attrs = ['apikey', 'org', 'login', 'raise_errors']
def _keep(m):
    return not m.startswith('_') and m not in _ignore_attrs
_api = API()
COLLECTIONS = [c for c in dir(_api) if _keep(c)] 
CMD_TREE = {c:[m.replace('_', '-') for m in dir(getattr(_api, c)) if _keep(m)] 
            for c in COLLECTIONS}

def install(parser):
    api_parser = parser.add_parser("api", help="Access API methods.")
    api_parser.add_argument('collection', type=str, help='The API collection to access.',
        choices=COLLECTIONS)
    api_parser.add_argument('method', type=str, default=None,
        help='The method for the collection. Use "ls" to list all methods for a given collection.')
    api_parser.add_argument("-d", dest="data", default=None, type=str,
        help="a .json / .yaml file, or a json string of the request's body")
    api_parser.add_argument("-e", "--raise-errors", action='store_true',
        default=False,
        help="Raise Errors as statements. If missing, will return JSON.")
    api_parser.add_argument('-u', '--api-url', type=str,
        default=os.getenv('NEWSLYNX_API_URL'), 
        help="The base url of Newslynx's API. Will default to $NEWSLYNX_API_URL")
    api_parser.add_argument('-k', '--apikey', dest="apikey", type=str,
        default=os.getenv('NEWSLYNX_API_KEY'), 
        help="Your API key. Will default to $NEWSLYNX_API_KEY")
    api_parser.add_argument('-o', '--org', dest="org", type=str, 
        help="The ID/Slug of the organization you'd like to access. "
             "Will default to $NEWSLYNX_API_ORG",
        default=os.getenv('NEWSLYNX_API_ORG'))

    return 'api', run


def run(opts, **kwargs):

    # connect to the api
    api = API(
        apikey=opts.apikey, 
        org=opts.org, 
        api_url=opts.api_url,
        raise_errors=opts.raise_errors)

    # get the collection
    cobj = getattr(api, opts.collection, None)
    if not cobj:
        e = RuntimeError("Error: Collection '{}' does not exist."
            .format(opts.collection))
        echo_error(e)
        echo("Choose from the following collections:\n\t- {}"
             .format(opts.collection, "\n\t- {}".join(COLLECTIONS)),
             color = fore.WHITE)
        sys.exit(1)

    # allow for `-` instead of `_`:
    if opts.method:
        opts.method = opts.method.replace('-', "_")

    mobj = getattr(cobj, opts.method, None)
    if not mobj:
        options = CMD_TREE[opts.collection]
        if opts.method != 'ls':
            e = RuntimeError("Method '{}' does not exist for collection '{}'"
                 .format(opts.method, opts.collection))
            echo_error(e, no_color=opts.no_color)
        else:
            echo("/{}".format(opts.collection), color=Fore.BLUE, no_color=opts.no_color)
        msg = "choose from the following methods:\n\t- {}"\
              .format( "\n\t- ".join(options))
        echo(msg, color=Fore.YELLOW, no_color=opts.no_color)
        sys.exit(1)

    # parse body file / json string.
    kwargs.update(load_data(opts.data, opts))
    
    # execute method
    try:
        res = mobj(**kwargs)
    
    except KeyboardInterrupt as e:
        echo_error("Interrupted by user. Exiting.", color=Fore.YELLOW, no_color=opts.no_color)
        sys.exit(2) # interrupt
    
    except Exception as e:
        tb = format_exc()
        echo_error(e, tb, no_color=opts.no_color)
        sys.exit(1)
    
    # stream output
    if isgenerator(res):
        for r in res:
            sys.stdout.write(serialize.obj_to_json(r) +"\n")
    # stream 
    else:
        sys.stdout.write(serialize.obj_to_json(res))
    sys.exit(0)







