"""
Report the version of newslynx.
"""
import logging 

log = logging.getLogger(__name__)

def setup(parser):
    parser.add_parser("version", help="Report the version.")
    return 'version', run


def run(opts, **kwargs):
    """
    Report the version.
    """
    import pkg_resources
    v = pkg_resources.get_distribution("newslynx").version + "\n"
    log.info("VERSION: " + v)
