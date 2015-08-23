"""
This module loads configurations from file / env variables and merges them with `newslynx.defaults`

Throughout the rest of `newslynx` you can accessing configurations
by importing this module:

    from newslynx import settings
    print settings.SUPER_USER_EMAIL
    >>> 'merlynne@newslynx.org'

If you prefer, you can also just import the CONFIG object:

    from newslynx.settings import CONFIG
    print CONFIG['super_user_email']
    >>> 'merlynne@newslynx.org'

"""
from traceback import format_exc
import sys
import os

from newslynx.exc import ConfigError
from newslynx.lib.serialize import yaml_stream_to_obj
from newslynx import defaults


def _load_config():
    """
    Load newslynx configurations from file / env variables.
    """
    # load config file
    config_file = os.getenv('NEWSLYNX_CONFIG_FILE', '~/.newslynx/config.yaml')
    if config_file.startswith('~'):
        config_file = os.path.expanduser(config_file)

    if not os.path.exists(config_file):
        raise ConfigError(
            "No Config could be found at '{}'."
            .format(config_file))
    try:
        config = yaml_stream_to_obj(open(config_file))

    except Exception as e:
        raise ConfigError(
            "There was an error loading config '{}'.\n"
            "Here is the error message:\n{}."
            .format(config_file, format_exc()))

    # update with environment variables
    for name, value in sorted(os.environ.items()):
        if name.startswith('NEWSLYNX_') and name != 'NEWSLYNX_CONFIG_FILE':
            name = name.replace('NEWSLYNX_', '').lower()
            config[name] = value

    # check for required config parametrics
    for k in defaults._CONFIG_REQUIRES:
        if k not in config:
            raise ConfigError(
                'Required setting "{}"" is missing from {} / ENV variables'
                .format(k, config_file))
    config['config_file'] = config_file
    return config


def _check_plugin(m, *args):
    """"
    Check if a plugin has been activated.
    """
    tests = []
    for a in args:
        # check for optional plugins
        if hasattr(m, a) and getattr(m, a, None):
            tests.append(True)
        else:
            tests.append(False)
    return all(tests)


# load config for file / environment
CONFIG = _load_config()

# setting configurations as globals to this module.
m = sys.modules[__name__]
for name, value in CONFIG.items():
    setattr(m, name.upper(), value)

# override missing options with defaults
for attr in dir(defaults):
    if not attr.startswith('__'):
        try:
            getattr(m, attr)
        except AttributeError:
            v = getattr(defaults, attr)
            # update config
            CONFIG[attr] = v
            setattr(m, attr, v)

# check for optional plugins
FB_ENABLED = _check_plugin(m, 'FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET')
CONFIG['fb_enabled'] = FB_ENABLED

TWT_ENABLED = _check_plugin(m, 'TWITTER_API_KEY', 'TWITTER_API_SECRET')
CONFIG['twt_enabled'] = TWT_ENABLED

GA_ENABLED = _check_plugin(
    m, 'GOOGLE_ANALYTICS_CLIENT_ID', 'GOOGLE_ANALYTICS_CLIENT_SECRET')
CONFIG['ga_enabled'] = GA_ENABLED

EMBEDLY_ENABLED = _check_plugin(m, 'EMBEDLY_API_KEY')
CONFIG['embedly_enabled'] = EMBEDLY_ENABLED

BITLY_ENABLED = _check_plugin(m, 'BITLY_ACCESS_TOKEN')
CONFIG['bitly_enabled'] = BITLY_ENABLED

PANDOC_ENABLED = _check_plugin(m, 'PANDOC_PATH')
CONFIG['pandoc_enabled'] = PANDOC_ENABLED

MAIL_ENABELD = _check_plugin(
    m, 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_SERVER',
    'SMTP_PORT', 'IMAP_PORT')
CONFIG['mail_enabled'] = MAIL_ENABELD
