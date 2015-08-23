"""
Run the cron daemon.
"""


def setup(parser):
    """
    Install this parser. Basic for now.
    """
    from newslynx.core import settings

    cron_parser = parser.add_parser(
        "cron", help="Spawns the dynamic scheduling daemon.")
    cron_parser.add_argument('-i', '--interval', dest='interval', help='The refresh interval',
                             type=int, default=settings.SCHEDULER_REFRESH_INTERVAL)
    return 'cron', run


def run(opts, **kwargs):
    from newslynx.scheduler import RecipeScheduler
    scheduler = RecipeScheduler(**kwargs)
    scheduler.run(**kwargs)
