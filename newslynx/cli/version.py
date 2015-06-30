import pkg_resources

from colorama import Fore

from newslynx.cli.common import echo

def setup(parser):
    api_parser = parser.add_parser("version", help="Report the version.")
    return 'version', run

def run(opts, log, **kwargs):
    """
    Report the version.
    """
    v = pkg_resources.get_distribution("newslynx").version
    log.info(v, line=False, color='magenta')