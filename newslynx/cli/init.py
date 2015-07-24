"""
Initialize Database, Super User, and Sous Chefs
"""
import os
import re
import sys

from newslynx.cli.common import LOGO
from newslynx.init import load_sql
from newslynx.views import app
from newslynx.core import db
from newslynx import settings
from newslynx.tasks import default

re_conf = '{}:[^\n]+'


def setup(parser):
    """
    Install this parser. Basic for now.
    """
    init_parser = parser.add_parser(
        "init",
        help="Initializes the database, super user, and core sous chefs.")
    init_parser = init_parser.add_argument(
        '--app-defaults', dest='app_defaults',
        action='store_true', default=False,
        help='Whether or not the initialize NewsLynx with the defaults that the App expects.')
    return 'init', run


def run(opts, log, **kwargs):
    # create the database
    log.info(LOGO + "\n", line=False, color='lightwhite_ex')
    with app.app_context():

        # import defaults
        from newslynx.defaults import (
            _DEFAULT_CONFIG, _CONFIG_REQUIRES, _DEFAULT_DEFAULTS)
        try:
            from newslynx.settings import CONFIG_FILE as config_file
            from newslynx.settings import DEFAULT_TAGS as tags_file
            from newslynx.settings import DEFAULT_RECIPES as recipes_file

        except Exception:
            from newslynx.defaults import CONFIG_FILE as default_config_file
            from newslynx.defaults import DEFAULT_TAGS as default_tags_file
            from newslynx.defaults import DEFAULT_RECIPES as default_recipes_file
            config_file = None
            tags_file = None
            recipes_file = None

        try:
            log.info('\nCreating database "{}"\n'.format(
                settings.SQLALCHEMY_DATABASE_URI), line=False)
            db.configure_mappers()
            db.create_all()

            log.info('\n(Re)Loading SQL Extensions\n', line=False)

            # load sql extensions + functions
            for sql in load_sql():
                db.session.execute(sql)

            # install app defaults.
            if opts.app_defaults:
                log.info('\nInitializing App Defaults\n', line=False)
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

                    log.info('\nStoring default ', line=False, color="yellow")
                    log.info(name, line=False, color='green')
                    log.info(' in:\n', line=False, color="blue")
                    log.info(m + "\n", line=False, color='magenta')

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

                log.info('\nStoring new configurations to:\n', line=False, color="blue")
                log.info(config_file + "\n", color='magenta', line=False)
                with open(config_file, 'wb') as f:
                    f.write(conf_str)

            log.info('\nInitializing Super User Org {}\n'.format(
                settings.SUPER_USER_ORG), line=False)
            default.org()

        except Exception as e:
            db.session.rollback()
            db.session.close()
            log.exception(e, tb=True)
            sys.exit(1)
        else:
            log.info('\nSuccess!\n', line=False)
            log.warning(
                '\nYou can now start the API by running ', color="blue", line=False)
            log.info('newslynx debug\n\n', color="green", line=False)
