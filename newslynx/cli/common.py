import re
import os
from copy import copy

from newslynx.lib import serialize

from newslynx.constants import (
    NULL_VALUES, TRUE_VALUES, FALSE_VALUES)

ACCEPTABLE_FILE_FORMATS = [
    'yml', 'yaml', 'json'
]

LOGO = """
 / \ / \ / \ / \ / \ / \ / \ / \ 
( n | e | w | s | l | y | n | x )
 \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/
"""

# lil' hacks.
re_quoted_arg = re.compile(r'^[\'\"]?(.*)[\'\"]?$')
trues = copy(TRUE_VALUES)
trues.remove('1')
falses = copy(FALSE_VALUES)
falses.remove('0')


def parse_runtime_args(arg_strings):
    """
    Parses arbitrary command-line args of the format:
    --option1=value1 -option2="value" -option3 value3
    Into a dictionary of:
    {'option1':'value1', 'option2':'value2', 'option3': 'value3'}
    """
    kwargs = {}
    for arg_string in arg_strings:
        parts = arg_string.split("=")
        key = parts[0].replace('-', '').strip()

        # assume this means a boolean flag
        if len(parts) == 1:
            kwargs[key] = True
        # clean
        else:
            m = re_quoted_arg.search("=".join(parts[1:]))
            value = m.group(0)
            if value in NULL_VALUES:
                kwargs[key] = None
            elif value in trues:
                kwargs[key] = True
            elif value in falses:
                kwargs[key] = False
            else:
                kwargs[key] = value
    return kwargs


def acceptable_file(path_or_string):
    for fmt in ACCEPTABLE_FILE_FORMATS:
        if path_or_string.lower().endswith('.{}'.format(fmt)):
            return True
    return False


def load_data(path_or_string):
    """
    Load data in from a filepath or a string
    """
    kwargs = {}
    if not path_or_string:
        return kwargs
    try:
        d = serialize.json_to_obj(path_or_string)
        kwargs.update(d)
        return kwargs

    except ValueError as e:
        # only deal with these formats.
        if not acceptable_file(path_or_string):
            raise ValueError(
                'You can only pass in .yaml, .yml, or .json files.')

        fp = os.path.expanduser(path_or_string)
        kwargs.update(serialize.yaml_to_obj(open(fp).read()))
        return kwargs
