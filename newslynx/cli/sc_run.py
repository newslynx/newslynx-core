"""
Create, Manage, and Install Sous Chef modules
"""
import os
import sys
from inspect import isgenerator
import logging

log = logging.getLogger(__name__)


def setup(parser):
    from newslynx.core import settings

    sc_parser = parser.add_parser('sc-run')
    sc_parser.add_argument('sous_chef',
                           type=str, help='The relative path to the sous chef configuration file.')
    sc_parser.add_argument('-r', "--recipe", dest='recipe',
                           help="a .json / .yaml file, or a json string of recipe options",
                           type=str, default=None)
    sc_parser.add_argument('-u', '--apiurl', dest='apiurl', type=str,
                           default=os.getenv(
                               'NEWSLYNX_API_URL', settings.API_URL),
                           help="The base url of Newslynx's API. Will default to $NEWSLYNX_API_URL")
    sc_parser.add_argument('-k', '--apikey', dest="apikey", type=str,
                           default=os.getenv(
                               'NEWSLYNX_APIKEY', settings.SUPER_USER_APIKEY),
                           help="Your API key. Will default to $NEWSLYNX_APIKEY")
    sc_parser.add_argument('-o', '--org', dest="org", type=str,
                           help="The ID/Slug of the organization you'd like to access. "
                           "Will default to $NEWSLYNX_ORG",
                           default=os.getenv('NEWSLYNX_ORG', settings.SUPER_USER_ORG))
    return 'sc-run', run


def run(opts, **kw):

    from newslynx.sc import sc_exec
    from newslynx.lib import serialize
    from newslynx.cli.common import load_data
    from newslynx.client import API

    # connect to the api and fetch org
    kw['apikey'] = opts.apikey
    kw['api_url'] = opts.apiurl

    api = API(
        apikey=opts.apikey,
        org=opts.org,
        api_url=opts.apiurl,
        raise_errors=True)
    try:
        kw['org'] = api.orgs.get(opts.org)
    except:
        log.warning('Cannot connect to the API. Running in dev mode.')
        kw['org'] = {'id': opts.org}

    # parse body file / json string.
    recipe = load_data(opts.recipe)
    if recipe:
        kw.update(recipe)

    res = sc_exec.run(opts.sous_chef, **kw)
    if not res:
        return
    # stream output
    if isgenerator(res):
        for r in res:
            sys.stdout.write(serialize.obj_to_json(r) + "\n")
    # stream
    else:
        sys.stdout.write(serialize.obj_to_json(res))
