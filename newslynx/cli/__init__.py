from gevent.monkey import patch_all 
patch_all()

import sys
import os
from inspect import isgenerator
from traceback import format_exc
import argparse

from colorama import Fore
from newslynx.cli.common import echo, echo_error, parse_runtime_args
from newslynx.logs import ColorLog 
from newslynx.exc import ConfigError


def setup(subparser):
    """
    Install all subcommands.
    """

    from newslynx.cli import api, version, dev, init, debug, cron
    MODULES = [
        api,
        dev,
        init,
        cron,
        version,
        debug
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
    try:
        # create an argparse instance
        parser = argparse.ArgumentParser(prog='newslynx/nlynx')
        parser.add_argument('--no-color', dest='no_color', action="store_true", 
            default=False, help='Disable colored logging.')

        # add the subparser "container"
        subparser = parser.add_subparsers(help='Subcommands', dest='cmd')
        subcommands = setup(subparser)
        
        # parse the arguments + options
        opts, kwargs = parser.parse_known_args()
        kwargs = parse_runtime_args(kwargs)

        # run the necessary subcommand
        if opts.cmd not in subcommands:
            subcommands
            echo_error(RuntimeError("No such subcommand."), no_color=opts.no_color)

        try:
            subcommands[opts.cmd](opts, log, **kwargs)

        except KeyboardInterrupt as e:
            log.warning('Interrupted by user, exiting', line=False)
            sys.exit(2) # interrupt

        except Exception as e:
            log.exception(e, tb=True)
            sys.exit(1)

    except ConfigError as e:
        log.exception(e, tb=False)


    except KeyboardInterrupt as e:
        log.warning('Interrupted by user, exiting', line=False)
        sys.exit(2) # interrupt

