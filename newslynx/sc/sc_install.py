"""
Install Sous Chef modules from git repositories
"""

import os
from git import Repo

from newslynx.core import settings
from newslynx.exc import SousChefInstallError


def fetch(git_url, sous_chef_dir=settings.SOUS_CHEF_DIR):

    # ensure sous chef dir exists
    if not os.path.exists(sous_chef_dir):
        os.makedirs(sous_chef_dir)

    # 
    pass

