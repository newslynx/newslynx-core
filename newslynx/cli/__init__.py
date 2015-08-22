"""
NewsLynx's CLI
"""

from gevent.monkey import patch_all
patch_all()

import sys
import argparse
from argparse import RawTextHelpFormatter

from newslynx.cli.common import parse_runtime_args
from newslynx.logs import ColorLog, StdLog
from newslynx.exc import ConfigError


def setup(parser):
    """
    Install all subcommands.
    """

    subparser = parser.add_subparsers(help='Subcommands', dest='cmd')

    from newslynx.cli import (
        api, db, version, dev, init,
        debug, cron, echo, sc_create,
        sc_docs, sc
    )
    MODULES = [
        api,
        sc,
        db,
        dev,
        init,
        echo,
        cron,
        version,
        debug,
        sc_create,
        sc_docs
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
    log = ColorLog()
    opts = None
    kwargs = {}
    try:
        # create an argparse instance
        parser = argparse.ArgumentParser(
            prog='newslynx/nlx', formatter_class=RawTextHelpFormatter)
        parser.add_argument('--no-color', dest='no_color', action="store_true",
                            default=False, help='Disable colored logging.')
        parser.add_argument('--no-interactive', dest='no_interactive', action="store_true",
                            default=False, help='Dont prompt for config.')

        # add the subparser "container"
        subcommands = setup(parser)

        # parse the arguments + options
        opts, kwargs = parser.parse_known_args()
        kwargs = parse_runtime_args(kwargs)

        if opts.no_color:
            log = StdLog()

        # run the necessary subcommand
        if opts.cmd not in subcommands:
            log.exception(
                RuntimeError("No such subcommand."), no_color=opts.no_color)

        try:
            subcommands[opts.cmd](opts, log, **kwargs)

        except KeyboardInterrupt as e:
            log.warning('\nInterrupted by user.\n', line=False)
            sys.exit(2)  # interrupt

        except Exception as e:
            log.exception(e, tb=True)
            sys.exit(1)

    except ConfigError as e:
        log.exception(e, tb=False, line=False)
        sys.exit(1)

    except KeyboardInterrupt as e:
        log.warning('\nInterrupted by user.\n', line=False)
        sys.exit(2)  # interrupt
