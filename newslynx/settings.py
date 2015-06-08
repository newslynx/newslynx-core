"""
Get Configurations from environment / config file.
"""
import sys
import os


from newslynx.exc import ConfigError
from newslynx.lib.serialize import yaml_stream_to_obj
from newslynx.util import check_plugin


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
    except Exception as e:
        raise ConfigError('There was an error loaing config "{}":\n{}'
                          .format(config_file, e.message))

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

# check for optional plugins
FB_ENABLED = check_plugin(m, 'FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET')
TWT_ENABLED = check_plugin(m, 'TWITTER_API_KEY', 'TWITTER_API_SECRET')
GA_ENABLED = check_plugin(
    m, 'GOOGLE_ANALYTICS_CLIENT_ID', 'GOOGLE_ANALYTICS_CLIENT_SECRET')
EMBEDLY_ENABLED = check_plugin(m, 'EMBEDLY_API_KEY')
BITLY_ENABLED = check_plugin(m, 'BITLY_ACCESS_TOKEN')
