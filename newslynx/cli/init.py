"""
Initialize Database, Super User, and Sous Chefs
"""

import sys

from newslynx.init import load_sous_chefs
from newslynx.cli.common import LOGO
from newslynx.models import sous_chef_schema
from newslynx.init import load_sql
from newslynx.models import User, SousChef
from newslynx.views import app
from newslynx.core import db
from newslynx import settings
from newslynx.tasks import default



def setup(parser):
    """
    Install this parser. Basic for now.
    """
    init_parser = parser.add_parser(
        "init",
        help="Initializes the database, super user, and core sous chefs.")
    return 'init', run


def run(opts, log, **kwargs):
    # create the database
    log.info(LOGO + "\n", line=False, color='lightwhite_ex')
    try:
        with app.app_context():
            log.info('Creating database "{}"\n'.format(
                settings.SQLALCHEMY_DATABASE_URI), line=False)
            db.configure_mappers()
            db.create_all()

            log.info('(Re)Loading SQL Extensions\n', line=False)

            # load sql extensions + functions
            for sql in load_sql():
                db.session.execute(sql)

            # commit
            db.session.commit()

            log.info('Initializing Super User Org {}\n'.format(settings.SUPER_USER_ORG), line=False)
            default.org()
            db.session.commit()
            db.session.close()

        log.info('\nSuccess!\n', line=False)
        log.warning(
            '\nYou can now start the API by running ', color="blue", line=False)
        log.info('newslynx debug\n\n', color="green", line=False)

    except Exception as e:
        db.session.rollback()
        db.session.close()
        log.exception(e, tb=True)
        sys.exit(1)
