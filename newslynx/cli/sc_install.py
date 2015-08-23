"""
Create, Manage, and Install Sous Chef modules
"""

from newslynx.sc import sc_module


def setup(parser):
    parser = parser.add_parser('sc-install')
    parser.add_argument('git_url',
                        type=str, help='The Sous Chef repository to install.')
    parser.add_argument('-u', '--update', dest='update', action='store_true',
                        help='Update an existing module.')
    return 'sc-install', run


def run(opts, **kw):
    """
    Install a Sous Chef module from GitHub.
    """
    sc_module.install(opts.git_url, update=opts.update)
    log.info('Now run $ newslynx sc-sync')
