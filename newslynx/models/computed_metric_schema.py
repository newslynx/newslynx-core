"""
TODO: validate formula strings for computed metrics by testing a SQL command within 
a read-only session and validating the results.
"""

import re
from newslynx.util import uniq

re_formula_metric_names = re.compile('{([a-z_]+)}')


def required_metrics(f):
    """
    What metrics does this formula require?
    """
    return uniq(re_formula_metric_names.findall(f))
