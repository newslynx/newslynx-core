import sys
import os
from inspect import isgenerator

import click
from colorama import Fore
import argparse

from newslynx.scheduler import RecipeScheduler
from newslynx import settings
from newslynx.cli.common import echo 


class CLIScheduler(RecipeScheduler):
    def __init__(self, opts, **kwargs):
        kwargs.update(opts.__dict__)
        RecipeScheduler.__init__(self, **kwargs)
        self.opts = opts
        self.kwargs = kwargs 

    def log(self, msg):
        return echo(msg, color=Fore.BLUE, no_color=self.opts.no_color)


def setup(parser):
    """
    Install this parser. Basic for now.
    """
    cron_parser = parser.add_parser("cron", help="Spawns the dynamic scheduling daemon.")
    cron_parser.add_argument('-r', '--refersh-interval', dest='interval',
        type=int, default=settings.SCHEDULER_REFRESH_INTERVAL)
    return 'cron', run

def run(opts, **kwargs):
    scheduler = CLIScheduler(opts, **kwargs)
    scheduler.run(**kwargs)