"""
Create, Manage, and Install Sous Chef modules
"""

from newslynx.sc import sc_sync
from newslynx.sc import sc_module

def setup(parser):
    parser = parser.add_parser('sc-sync')
    return 'sc-sync', run


def run(opts, **kw):
    """
    Sync all sous chefs for all organizations.
    """
    for u in opts.git_urls:
        sc_module.install(u)
    sc_sync.orgs()
