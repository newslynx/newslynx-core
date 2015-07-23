"""
Run the cron daemon.
"""


def setup(parser):
    """
    Install this parser. Basic for now.
    """
    from newslynx import settings

    cron_parser = parser.add_parser(
        "cron", help="Spawns the dynamic scheduling daemon.")
    cron_parser.add_argument('-i', '--interval', dest='interval', help='The refresh interval',
                             type=int, default=settings.SCHEDULER_REFRESH_INTERVAL)
    return 'cron', run


def run(opts, log, **kwargs):
    from newslynx.scheduler import RecipeScheduler
    scheduler = RecipeScheduler(log=log, **kwargs)
    scheduler.run(**kwargs)
