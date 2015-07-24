"""
access configurations
"""
from newslynx import settings
import sys


def setup(parser):
    """
    Install this parser. Basic for now.
    """
    cron_parser = parser.add_parser("echo", help="Prints configuation variables.")
    cron_parser.add_argument('name', type=str)
    return 'echo', run


def run(opts, log, **kwargs):
    v = getattr(settings, opts.name.replace('-', "_").upper().strip(), None)
    if not v:
        log.error('Config parameter "{}" does not exist.\n'.format(opts.name), line=False)
        sys.exit(1)
    log.info(v, line=False, color="blue")
    log.info("\n", line=False)
    sys.exit(0)