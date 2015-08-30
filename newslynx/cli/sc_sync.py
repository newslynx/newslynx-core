"""
Create, Manage, and Install Sous Chef modules
"""
from newslynx.sc import sc_sync


def setup(parser):
    parser = parser.add_parser('sc-sync')
    return 'sc-sync', run


def run(opts, **kw):
    """
    Sync all sous chefs for all organizations.
    """
    sc_sync.orgs()
