"""
Generate a SousChef module from a template directory.
"""

import os
from jinja2 import Template

from newslynx.util import here, recursive_listdir
from newslynx.lib.text import slug


DEFAULT_TMPL_DIR = here(__file__, 'template/')


def create(**kw):
    """
    Create a SousChef Module from a directory of Jinja Templates.
    """
    # get root dir
    root_dir = "{root_dir}/{slug}/".format(**kw)
    module_dir = "{}{name}/".format(root_dir, **kw)
    if not os.path.exists(module_dir):
        os.makedirs(module_dir)

    # create __init__.py
    init_py_path = os.path.join(module_dir, '__init__.py')
    if not os.path.exists(init_py_path):
        open(init_py_path, 'a').close()

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
                    if not os.path.exists(new_path):
                        with open(new_path, 'wb') as fh:
                            fh.write(contents)
                    break

                except IOError:
                    d = "/".join(new_path.split('/')[:-1])
                    if not os.path.exists(d):
                        os.makedirs(d)
