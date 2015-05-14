"""
Get Configurations from environment / config file.
"""
import sys
import os


from newslynx.exc import ConfigError
from newslynx.lib.serialize import yaml_stream_to_obj


def load_config():
    """
    Load newslynx configurations from file / env variables.
    """
    # load config file
    config_file = os.getenv('NEWSLYNX_CONFIG_FILE', '~/.newslynx/config.yaml')
    if config_file.startswith('~'):
        config_file = os.path.expanduser(config_file)

    if not os.path.exists(config_file):
        raise ConfigError(
            'No NewsLynx Config could be found at {}'.format(config_file))
    try:
        config = yaml_stream_to_obj(open(config_file))
    except Exception:
        raise ConfigError('There was an error loding config: {}'
                          .format(config_file))

    # update with environment variables
    for name, value in sorted(os.environ.items()):
        if name.startswith('NEWSLYNX_') and name != 'NEWSLYNX_CONFIG_FILE':
            name = name.replace('NEWSLYNX_', '').lower()
            config[name] = value
    return config


# load config for file / environment
config = load_config()


# setting configurations as globals
m = sys.modules[__name__]
for name, value in config.items():
    setattr(m, name.upper(), value)
