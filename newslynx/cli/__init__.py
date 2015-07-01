"""
NewsLynx's CLI
"""

from gevent.monkey import patch_all 
patch_all()

import sys
import os
from inspect import isgenerator
from traceback import format_exc
import argparse

from sqlalchemy import create_engine
from colorama import Fore

from newslynx.cli.common import parse_runtime_args
from newslynx.logs import ColorLog, StdLog
from newslynx.exc import ConfigError

LOGO = """
 / \ / \ / \ / \ / \ / \ / \ / \ 
( n | e | w | s | l | y | n | x )
 \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/
"""  

def setup(subparser):
    """
    Install all subcommands.
    """

    from newslynx.cli import api, version, dev, init, debug, cron, config, echo
    MODULES = [
        api,
        dev,
        init,
        echo,
        cron,
        config,
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
    opts = None 
    kwargs = {}
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

        if opts.no_color:
            log = StdLog()

        # run the necessary subcommand
        if opts.cmd not in subcommands:
            subcommands
            echo_error(RuntimeError("No such subcommand."), no_color=opts.no_color)

        try:
            subcommands[opts.cmd](opts, log, **kwargs)

        except KeyboardInterrupt as e:
            log.warning('\nInterrupted by user.\n', line=False)
            sys.exit(2) # interrupt

        except Exception as e:
            log.exception(e, tb=True)
            sys.exit(1)

    except ConfigError as e:
        from newslynx.cli import config 
        log.info(LOGO +"\n", line=False, color='lightwhite_ex')
        log.exception(e, tb=False, line=False)
        log.info("\n\n", line=False)
        kwargs['re'] = False
        config.run(opts, log, **kwargs)

    except KeyboardInterrupt as e:
        log.warning('\nInterrupted by user.\n', line=False)
        sys.exit(2) # interrupt

