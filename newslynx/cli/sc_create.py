"""
Create, Manage, and Install Sous Chef modules
"""
import logging

from newslynx.sc import sc_module
from newslynx.util import here
from newslynx.lib.text import slug


log = logging.getLogger(__name__)


def setup(parser):
    parser = parser.add_parser('sc-create')
    parser.add_argument('module_name',
                        type=str, help='The name / relative directory of the SousChef to create.')
    parser.add_argument('-g', '--github-user', dest='github_user',
                        type=str, help='The author\'s github user name.',
                        default='newslynx')
    parser.add_argument('-d', '--description', dest='description', type=str,
                        help='A short description of the Sous Chef module', default="")
    parser.add_argument('-a', '--author', type=str,
                        dest='author', default='Merlynne')
    parser.add_argument('-t', '--template', dest='template', type=str,
                        help='A path to a module template. Defaults to built-in template.', default=None)
    parser.add_argument('-u', '--update', dest='update', action="store_true",
                        help='Whether or not to overwrite existing files')
    return 'sc-create', run


def run(opts, **kw):

    # parse paths
    if not '/' in opts.module_name:
        root_dir = here('.')
        _slug = slug(opts.module_name)
    else:
        parts = opts.module_name.split('/')
        root_dir = "/".join(parts[:1])
        _slug = slug(parts[-1])

    kw.update({
        'root_dir': root_dir,
        'name': _slug.replace('-', '_'),
        'slug': _slug,
        'description': opts.description,
        'github_user': opts.github_user,
        'author': opts.author,
        'update': opts.update
    })
    if opts.template:
        kw['tmpl_dir'] = opts.template
    log.info(
        'Creating Sous Chef Module: {}'.format(opts.module_name))
    sc_module.create(**kw)
