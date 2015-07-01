"""
access configurations
"""

import sys 

def setup(parser):
    """
    Install this parser. Basic for now.
    """
    from newslynx import settings

    cron_parser = parser.add_parser("echo", help="Prints configuation variables.")
    cron_parser.add_argument('name', type=str)
    return 'echo', run

def run(opts, log, **kwargs):
    from newslynx import settings
    all_settings = [s for s in dir(settings) if not s.startswith('_')]
    
    v = getattr(settings, opts.name.replace('-', "_").upper().strip(), None)
    if not v:
        log.error('Config parameter "{}" does not exist.\n'.format(opts.name), line=False)
        sys.exit(1)
    log.info(v, line=False, color="blue")
    log.info("\n", line=False)
    sys.exit(0)


