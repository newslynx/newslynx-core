"""
TODO: validate formula strings for computed metrics.
"""
import re
from newslynx.util import uniq

re_formula_metric_names = re.compile('{([a-z_]+)}')


def required_metrics(f):
    """
    What metrics does this formula require?
    """
    return uniq(re_formula_metric_names.findall(f))
