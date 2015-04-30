import os
from collections import OrderedDict

from newslynx.lib.serialize import yaml_stream_to_obj


def load_config():
    """
    Load newslynx configurations from file / env variables.
    """
    # load config file
    config_file = os.getenv('NEWSLYNX_CONFIG_FILE')
    if config_file:
        config = yaml_stream_to_obj(open(config_file))
    else:
        config = OrderedDict()

    # update with environment variables
    for name, value in sorted(os.environ.items()):
        if name.startswith('NEWSLYNX_') and name != 'NEWSLYNX_CONFIG_FILE':
            name = name.replace('NEWSLYNX_', '').lower()
            config[name] = value
    return config
