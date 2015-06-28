from gevent.monkey import patch_all 
patch_all()

import sys
import os
from inspect import isgenerator
from traceback import format_exc
import argparse

from colorama import Fore

from newslynx.cli import api, version, dev, init, debug
from newslynx.cli.common import echo, echo_error, parse_runtime_args

MODULES = [
    api,
    dev,
    init,
    version,
    debug
]

def install_subcommands(subparser):
    """
    Install all subcommands.
    """
    subcommands = {}
    for module in MODULES:
        cmd_name, run_func = module.install(subparser)
        subcommands[cmd_name] = run_func
    return subcommands

def run():
    """
    The main cli function.
    """
    # create an argparse instance
    parser = argparse.ArgumentParser(prog='newslynx')

    # add the subparser "container"
    subparser = parser.add_subparsers(help='sub-command help', dest='cmd')
    subcommands = install_subcommands(subparser)
    
    # parse the arguments + options
    opts, kwargs = parser.parse_known_args()
    kwargs = parse_runtime_args(kwargs)

    # run the necessary subcommand
    if opts.cmd not in subcommands:
        subcommands
        echo_error(RuntimeError("No such subcommand."))

    try:
        subcommands[opts.cmd](opts, **kwargs)
    except KeyboardInterrupt as e:
        echo('Interrupted by user, exiting', color=Fore.YELLOW)
        sys.exit(2) # interrupt
    except Exception as e:
        tb = format_exc()
        echo_error(e, tb)
        sys.exit(1)
