"""
Initialize Database, Super User, and Sous Chefs
"""
import os
import re
import sys
import logging
from traceback import format_exc

from newslynx.cli.common import LOGO
from newslynx.init import load_sql
from newslynx.views import app
from newslynx.core import db
from newslynx.tasks import default

re_conf = '{}:[^\n]+'

log = logging.getLogger(__name__)


def setup(parser):
    """
    Install this parser. Basic for now.
    """
    init_parser = parser.add_parser(
        "init",
        help="Initializes the database, super user, and core sous chefs.")
    init_parser.add_argument(
        '--bare', dest='bare',
        action='store_true', default=False,
        help='Dont include the defaults for newslynx-app')
    init_parser.add_argument('--dev', dest="dev",
                             action="store_true",
                             help='An argument for the project\'s Makefile.')
    return 'init', run


def run(opts, **kwargs):
    # create the database
    if opts and not opts.log_type == 'json' and not opts.dev:
        print LOGO
    with app.app_context():

        # import defaults
        from newslynx.defaults import _CONFIG_REQUIRES, _DEFAULT_DEFAULTS
        from newslynx.settings import CONFIG_FILE as config_file
        from newslynx.settings import DEFAULT_TAGS as tags_file
        from newslynx.settings import DEFAULT_RECIPES as recipes_file
        from newslynx.core import settings

        try:
            log.info('(Re)Creating database "{}"'.format(
                settings.SQLALCHEMY_DATABASE_URI))
            db.configure_mappers()
            db.create_all()

            log.info('(Re)Loading SQL Extensions')

            # load sql extensions + functions
            for sql in load_sql():
                db.session.execute(sql)
            # install app defaults.
            if (not opts or not opts.bare) and not kwargs.get('empty', False):
                if not kwargs.get('empty', False):
                    log.info('(Re)Initializing App Defaults')
                modules = [
                    ('default_tags', tags_file),
                    ('default_recipes', recipes_file)
                ]
                conf_str = open(config_file).read()
                for k, m in modules:
                    m = os.path.expanduser(m)
                    parts = m.split('/')
                    default_dir = "/".join(parts[:-1])

                    path = parts[-1]
                    name = parts[-1].split('.')[0]
                    try:
                        os.makedirs(default_dir)
                    except OSError:
                        pass

                    log.info(
                        'Storing default {} in: {}'.format(name, config_file))

                    with open(m, 'wb') as f1:
                        with open(os.path.join(_DEFAULT_DEFAULTS, path), 'rb') as f2:
                            f1.write(f2.read())

                    cx = re.compile(re_conf.format(k))
                    newval = "{}: {}".format(k, m)
                    m = cx.search(conf_str)
                    if m:
                        conf_str = cx.sub(newval, conf_str)
                    else:
                        conf_str += "\n" + newval
                if not kwargs.get('empty', False):
                    log.info(
                        'Storing new configurations to: {}'.format(config_file))
                with open(config_file, 'wb') as f:
                    f.write(conf_str)

            if not kwargs.get('empty', False):
                log.info(
                    '(Re)Initializing Super User Org {}'.format(settings.SUPER_USER_ORG))
                default.org()

        except Exception as e:
            db.session.rollback()
            db.session.close()
            log.error(format_exc())
            sys.exit(1)

        else:
            if not kwargs.get('empty', False):
                log.info('Success!')
                log.info(
                    'You can now start the API by running: $ newslynx debug')
