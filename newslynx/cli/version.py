"""
Report the version of newslynx.
"""

def setup(parser):
    api_parser = parser.add_parser("version", help="Report the version.")
    return 'version', run

def run(opts, log, **kwargs):
    """
    Report the version.
    """
    import pkg_resources
    v = pkg_resources.get_distribution("newslynx").version + "\n"
    log.info(v, line=False, color='blue')