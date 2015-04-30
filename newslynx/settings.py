"""
Get Configurations from environment / config file.
"""
import sys

from newslynx.util import load_config

# load config for file / environment
config = load_config()

# setting configurations as globals
m = sys.modules[__name__]
for name, value in config.items():
    setattr(m, name.upper(), value)
