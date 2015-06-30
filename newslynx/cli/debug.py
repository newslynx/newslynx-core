import sys
import os
from inspect import isgenerator

import click
from colorama import Fore
import argparse

from newslynx.cli.common import echo, echo_error, load_data
from newslynx.views import app
from newslynx import settings


def setup(parser):
    """
    Mimics functionality of Flask-Script
    """
    srv_parser = parser.add_parser("debug", help="Run the development server.")
    srv_parser.add_argument('--host', dest="host", default='127.0.0.1', help="The API's address")
    srv_parser.add_argument('--port', dest="port", default=settings.API_PORT, type=int, help="The API's Port")
    srv_parser.add_argument('-e', '--raise-errors', dest="passthrough_errors", 
        action="store_true", default=False, help="Enables Flask's debugger.")
    return 'debug', run


def run(opts, log, **kwargs):
    """
    Runs the debug server.
    """
    app.run(host=opts.host,
            port=int(opts.port),
            debug=opts.passthrough_errors,
            use_debugger=opts.passthrough_errors,
            threaded=False,
            processes=False,
            use_reloader=False,
            passthrough_errors=opts.passthrough_errors)
