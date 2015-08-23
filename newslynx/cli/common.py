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
    if not path_or_string:
        return {}

    # treat it as a file first
    if acceptable_file(path_or_string):
        fp = os.path.expanduser(path_or_string)
        try:
            return serialize.yaml_to_obj(open(fp).read())
        except Exception as e:
            raise IOError(
                "Could not read file '{}' \n{}"
                .format(fp, e.message))

    # otherwise assume it's a JSON blob
    else:
        try:
            return serialize.json_to_obj(path_or_string)

        except ValueError as e:
            raise ValueError(
                "Could not parse JSON string '{}' \n{}"
                .format(path_or_string, e.message))
