import os
import sys
from inspect import isgenerator

# build up collections and command tree.
_ignore_attrs = ['apikey', 'org', 'login', 'raise_errors']
def _keep(m):
    return not m.startswith('_') and m not in _ignore_attrs


def setup(parser):
    
    # dynamically list collections
    from newslynx.client import API
    _api = API()
    COLLECTIONS = [c for c in dir(_api) if _keep(c)]

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


def run(opts, log, **kwargs):
    
    from newslynx.lib import serialize
    from newslynx.cli.common import load_data

    # dynamically list collections
    from newslynx.client import API

    # connect to the api
    api = API(
        apikey=opts.apikey, 
        org=opts.org, 
        api_url=opts.api_url,
        raise_errors=opts.raise_errors)

    # get the collection
    cobj = getattr(api, opts.collection, None)
    if not cobj:
        e = RuntimeError("Collection '{}' does not exist."
            .format(opts.collection))
        log.exception(e, tb=False)
        log.warning("Choose from the following collections:\n\t- {}"
             .format(opts.collection, "\n\t- {}".join(COLLECTIONS)), line=False)
        sys.exit(1)


    # allow for `-` instead of `_`:
    if opts.method:
        opts.method = opts.method.replace('-', "_")

    mobj = getattr(cobj, opts.method, None)
    if not mobj:
        
        COLLECTIONS = [c for c in dir(api) if _keep(c)]
        
        # compute the tree here to save on processing time.
        CMD_TREE = {c:[m.replace('_', '-') for m in dir(getattr(api, c)) if _keep(m)] 
                    for c in COLLECTIONS}
        options = CMD_TREE[opts.collection]
        
        if opts.method != 'ls':
            e = RuntimeError("Method '{}' does not exist for collection '{}'"
                 .format(opts.method, opts.collection))
            log.exception(e, tb=False)
        
        else:
            log.info("/{}\n".format(opts.collection), line=False, color='blue')
        
        msg = "choose from the following methods:\n\t- {}"\
            .format( "\n\t- ".join(options))
        log.warning(msg, line=False)
        sys.exit(1)

    # parse body file / json string.
    d = load_data(opts.data)
    kwargs.update(d)
    
    # execute method
    try:
        res = mobj(**kwargs)
    
    except KeyboardInterrupt as e:
        log.warning("Interrupted by user.\n", line=False)
        sys.exit(2) # interrupt
    
    except Exception as e:
        log.exception(e, tb=True)
        sys.exit(1)

    # stream output
    if isgenerator(res):
        for r in res:
            sys.stdout.write(serialize.obj_to_json(r) +"\n")
    # stream 
    else:
        sys.stdout.write(serialize.obj_to_json(res))
    sys.exit(0)







