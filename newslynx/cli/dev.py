"""
Random Development Tasks.
"""
from newslynx.dev import random_data
from newslynx.cli.common import echo
from newslynx.models import URLCache, ExtractCache, ThumbnailCache
from newslynx.models import ComparisonsCache

def setup(parser):
    tasks = run(None, _install=True)
    dev_parser = parser.add_parser("dev", help="Development utilities.")
    dev_parser.add_argument('task', type=str, help='The develpment task to run.', choices=tasks)
    return 'dev', run

def run(opts, log, **kwargs):
    tasks = {
        'gen-random-data': run_random_data,
        'flush-comparison-cache': run_flush_comparison_cache,
        'flush-extract-cache': run_flush_extract_cache
    }
    if kwargs.get('_install'):
        return tasks
    return tasks.get(opts.task.replace('_', '-'))(opts, **kwargs)

def run_random_data(opts, log, **kwargs):
    """
    Generate random data to play with.
    """
    return random_data.run(**kwargs)

def run_flush_comparison_cache(opts, log, **kwargs):
    """
    Flush the comparison cache.
    """
    ComparisonsCache.flush()
    log.info('Compaison cache flushed.')

def run_flush_extract_cache(opts, log, **kwargs):
    """
    Flush the extraction cache.
    """
    URLCache.flush()
    ExtractCache.flush()
    ThumbnailCache.flush()
    log.info('Extraction caches flushed.')




