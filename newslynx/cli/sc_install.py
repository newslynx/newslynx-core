"""
Create, Manage, and Install Sous Chef modules
"""
import logging

from newslynx.sc import sc_module

log = logging.getLogger(__name__)


def setup(parser):
    parser = parser.add_parser('sc-install')
    parser.add_argument('git_urls', nargs="+",
                        type=str, help='The Sous Chef repository to install.')
    parser.add_argument('--dev', dest="dev",
                        action="store_true",
                        help='An argument for the project\'s Makefile.')
    return 'sc-install', run


def run(opts, **kw):
    """
    Install a Sous Chef module from GitHub.
    """
    for u in opts.git_urls:
        sc_module.install(u)
    if not opts.dev:
        log.info('Now run $ newslynx sc-sync')
