"""
Random Development Tasks.
"""
from newslynx.dev import random_data
from newslynx.cli.common import echo
from newslynx.models import URLCache, ExtractCache, ThumbnailCache
from newslynx.models import ComparisonsCache

def install(parser):
    tasks = run(None, _install=True)
    dev_parser = parser.add_parser("dev", help="Development utilities.")
    dev_parser.add_argument('task', type=str, help='The develpment task to run.', choices=tasks)
    return 'dev', run

def run(opts, **kwargs):
    tasks = {
        'gen-random-data': run_random_data,
        'flush-comparison-cache': run_flush_comparison_cache,
        'flush-extract-cache': run_flush_extract_cache
    }
    if kwargs.get('_install'):
        return tasks
    return tasks.get(opts.task.replace('_', '-'))(opts, **kwargs)

def run_random_data(opts, **kwargs):
    """
    Generate random data to play with.
    """
    return random_data.run(**kwargs)

def run_flush_comparison_cache(opts, **kwargs):
    """
    Flush the comparison cache.
    """
    ComparisonsCache.flush()
    echo('Compaison cache flushed.', no_color=opts.no_color)

def run_flush_extract_cache(opts, **kwargs):
    """
    Flush the extraction cache.
    """
    URLCache.flush()
    ExtractCache.flush()
    ThumbnailCache.flush()
    echo('Extraction caches flushed.', no_color=opts.no_color)




