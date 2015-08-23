"""
access configurations
"""
import sys
import logging

log = logging.getLogger(__name__)


def setup(parser):
    """
    Install this parser. Basic for now.
    """
    cron_parser = parser.add_parser(
        "echo", help="Prints configuation variables.")
    cron_parser.add_argument('name', type=str)
    return 'echo', run


def run(opts, **kwargs):
    from newslynx.core import settings
    v = getattr(settings, opts.name.replace('-', "_").upper().strip(), None)
    if not v:
        log.error('Config parameter "{}" does not exist.\n'.format(opts.name))
        sys.exit(1)
    log.info(v)
    sys.exit(0)
