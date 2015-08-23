"""
Create, Manage, and Install Sous Chef modules
"""

from newslynx.init import load_sous_chefs
from newslynx.sc import sc_docs


def setup(parser):
    parser = parser.add_parser('sc-docs')
    parser.add_argument('module_path',
                        type=str, help='The path to the directory which contains Sous Chef configurations.')
    parser.add_argument('-f', '--format', dest='format', default='md', choices=['md', 'rst', 'pdf'],
                        type=str, help='The format of documentation to generate.')
    return 'sc-docs', run


def run(opts, **kw):

    for sc, fp in load_sous_chefs(sous_chef_dir=opts.module_path, incl_internal=False):
        print sc_docs.create(sc, fp, opts.format)
