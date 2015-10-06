"""
Generate a SousChef module from a template directory.
"""

import os
import logging
from traceback import format_exc
import pip

from jinja2 import Template
from git import Repo

from newslynx.util import here
from newslynx.core import settings
from newslynx.exc import SousChefInstallError

log = logging.getLogger(__name__)


DEFAULT_TMPL_DIR = here(__file__, 'template/')


DUMMY_SOUS_CHEF_CLASS = """
import os
from newslynx.sc import SousChef

class SayMyName(SousChef):

    def run(self):
        msg = 'Hello {my_name}!'.format(**self.options)
        os.system("say '{}'".format(msg))
        self.log.info(msg)
        return self.options

"""


DUMMY_SOUS_CHEF_CONFIG = """
name: Say My Name
slug: say-my-name
description: Conveniently says your name.
runs: {name}.SayMyName
options:
    my_name:
        input_type: text
        value_types:
            - string
        required: true
        help:
            description: Your name
            placeholder: Merlynne
"""


def create(**kw):
    """
    Create a SousChef Module from a directory of Jinja Templates.
    """

    update = kw.pop('update', False)

    # get root dir
    root_dir = "{root_dir}/{slug}/".format(**kw)
    module_dir = "{}{name}/".format(root_dir, **kw)
    if not os.path.exists(module_dir) and not update:
        os.makedirs(module_dir)

    # create __init__.py
    init_py_path = os.path.join(module_dir, '__init__.py')
    if not os.path.exists(init_py_path) and not update:
        with open(init_py_path, 'wb') as f:
            f.write(DUMMY_SOUS_CHEF_CLASS)

    # create say_my_name.yaml
    config_path = os.path.join(module_dir, 'say_my_name.yaml')
    if not os.path.exists(config_path) and not update:
        with open(config_path, 'wb') as f:
            f.write(DUMMY_SOUS_CHEF_CONFIG.format(**kw))

    # get tmpl_dir
    tmpl_dir = kw.get('tmpl_dir', DEFAULT_TMPL_DIR)
    if not tmpl_dir.endswith('/'):
        tmpl_dir += "/"

    # walk tmpl dir and populate module.
    for dir_name, dir_list, file_list in os.walk(tmpl_dir):
        # copy over files, optionally applying templating
        for filename in file_list:

            # if somehow a DS_Store or pyc gets in here during dev, skip it
            if 'DS_Store' in filename \
                    or '.pyc' in filename \
                    or filename == "__init__.py":
                continue

            old_path = os.path.join(dir_name, filename)
            new_path = old_path.replace(tmpl_dir, root_dir)

            tmpl = Template(open(old_path).read())
            contents = tmpl.render(**kw)
            # write the file
            while True:
                try:
                    if not update:
                        if not os.path.exists(new_path):
                            with open(new_path, 'wb') as fh:
                                fh.write(contents)
                    else:
                        with open(new_path, 'wb') as fh:
                            fh.write(contents)
                    break

                except IOError:
                    d = "/".join(new_path.split('/')[:-1])
                    if not os.path.exists(d):
                        os.makedirs(d)


def install(git_url, sous_chef_dir=settings.SOUS_CHEFS_DIR, **kw):
    """
    Fetch a git repository and store in the sous chef directory.
    Then install it via pip
    """

    # ensure directory format
    sous_chef_dir = os.path.expanduser(sous_chef_dir)
    if not sous_chef_dir.endswith('/'):
        sous_chef_dir += "/"

    # ensure sous chef dir exists
    if not os.path.exists(sous_chef_dir):
        log.warning('Creating directory: {}'.format(sous_chef_dir))
        os.makedirs(sous_chef_dir)

    # get module name:
    try:
        name = git_url.split('/')[-1].split('.')[0]
    except Exception as e:
        raise SousChefInstallError(
            'Could not parse git_url: {}'.format(git_url))

    # absolute directory of the Repo
    repo_dir = "{}{}".format(sous_chef_dir, name)

    # pull existing module
    exists = False
    if os.path.exists(repo_dir):
        exists = True
        repo = Repo(repo_dir)
        log.warning('Pulling latest version of "{}"'.format(git_url))
        o = repo.remotes.origin
        o.pull()

    # clone new module
    else:
        log.info('Cloning "{}" ==> "{}"'.format(git_url, repo_dir))
        try:
            Repo.clone_from(git_url, repo_dir)
        except Exception as e:
            raise SousChefInstallError(
                'Could not clone {}: {}'.format(git_url, format_exc()))

    if exists:
        log.warning('Reinstalling: {}'.format(name))
    else:
        log.info('Installing: {}'.format(name))
    sys_exit = pip.main(['install', '-e', repo_dir, '-q'])
    if sys_exit != 0:
        log.error('Could not install: {}'.format(name))
    else:
        if exists:
            log.warning('Successfully resintalled: {}'.format(name))
        else:
            log.info('Successfully installed: {}'.format(name))
    return True


def update(local_path, sous_chef_dir=settings.SOUS_CHEFS_DIR):
    """
    Update a sous chef module given it's local path.
    """
    # ensure directory format
    sous_chef_dir = os.path.expanduser(sous_chef_dir)
    if not sous_chef_dir.endswith('/'):
        sous_chef_dir += "/"

    repo_dir = "{}{}".format(sous_chef_dir, local_path)
    log.warning('Pulling latest version of "{}"'.format(repo_dir))
    repo = Repo(repo_dir)
    o = repo.remotes.origin
    o.pull()

    sys_exit = pip.main(['install', '-e', repo_dir, '-q'])
    if sys_exit != 0:
        log.error('Could not install: {}'.format(local_path))
    else:
        log.info('Successfully installed: {}'.format(local_path))


def update_all(sous_chef_dir=settings.SOUS_CHEFS_DIR):
    """
    Update all sous chef modules.
    """
    for local_path in os.listdir(os.path.expanduser(sous_chef_dir)):
        update(local_path, sous_chef_dir)
