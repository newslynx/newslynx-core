"""
NewsLynx's CLI
"""

from gevent.monkey import patch_all
patch_all()

import os
import sys
import argparse
import logging
from traceback import format_exc
from argparse import RawTextHelpFormatter

from newslynx.cli.common import parse_runtime_args, LOGO
from newslynx.exc import ConfigError


log = logging.getLogger(__name__)


def setup(parser):
    """
    Install all subcommands.
    """

    subparser = parser.add_subparsers(help='Subcommands', dest='cmd')

    from newslynx.cli import (
        api, db, version, dev, init,
        debug, cron, echo, sc_create,
        sc_docs, sc_run, sc_sync, sc_install
    )
    MODULES = [
        api,
        sc_run,
        db,
        dev,
        init,
        echo,
        cron,
        version,
        debug,
        sc_create,
        sc_docs,
        sc_sync,
        sc_install
    ]
    subcommands = {}
    for module in MODULES:
        cmd_name, run_func = module.setup(subparser)
        subcommands[cmd_name] = run_func
    return subcommands


def run():
    """
    The main cli function.
    """
    opts = None
    kwargs = {}
    try:
        from newslynx import settings
        from newslynx import logs

        # create an argparse instance
        parser = argparse.ArgumentParser(prog='newslynx/nlx',
                                         formatter_class=RawTextHelpFormatter)
        parser.add_argument('--log-type', dest='log_type', type=str,
                            default=settings.LOG_TYPE, help='The log format type.',
                            choices=['color', 'std', 'json'])
        parser.add_argument('--log-level', dest='log_level', type=str,
                            default=settings.LOG_LEVEL, help='The logging level to filter below.',
                            choices=['debug', 'info', 'warning', 'error', 'critical'])
        parser.add_argument('--log-datefmt', dest='log_datefmt', type=str,
                            default=settings.LOG_DATE_FORMAT, help='The date format to display.')

        # add the subparser "container"
        subcommands = setup(parser)

        # parse the arguments + options
        opts, kwargs = parser.parse_known_args()
        kwargs = parse_runtime_args(kwargs)

        # setup logging
        logs.setup_logger(level=opts.log_level,
                          datefmt=opts.log_datefmt,
                          type=opts.log_type)

        # check for proper subcommands
        if opts.cmd not in subcommands:
            log.error("No such subcommand.")

        try:
            subcommands[opts.cmd](opts, **kwargs)

        except KeyboardInterrupt as e:
            log.warning('Interrupted by user.')
            sys.exit(2)  # interrupt

        except Exception as e:
            log.error(format_exc())
            sys.exit(1)

    except ConfigError as e:

        from newslynx import defaults
        from newslynx import logs
        # setup default logging
        logs.setup_logger(level=defaults.LOG_LEVEL,
                          datefmt=defaults.LOG_DATE_FORMAT,
                          type=defaults.LOG_TYPE)
        print LOGO

        # make .newslynx folder
        d = defaults.CONFIG_FILE.replace('config.yaml', '').strip()
        if not os.path.exists(d):
            log.info('Creating directory {}'.format(d))
            os.makedirs(d)

        # setup default config
        if not os.path.exists(defaults.CONFIG_FILE):
            log.warning(
                'Moving default config to: {}'.format(defaults.CONFIG_FILE))
            with open(defaults.CONFIG_FILE, 'wb') as f:
                f.write(open(defaults._DEFAULT_CONFIG).read())

        # give more info
        from newslynx.cli import init
        init.run(opts, empty=True)

    except KeyboardInterrupt:
        log.warning('Interrupted by user.')
        sys.exit(2)  # interrupt
