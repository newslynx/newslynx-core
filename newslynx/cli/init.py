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

            # create the super user
            u = User.query.filter_by(email=settings.SUPER_USER_EMAIL).first()
            if not u:
                log.info('Creating super user "{}"\n'.format(
                    settings.SUPER_USER_EMAIL), line=False)
                u = User(name=settings.SUPER_USER,
                         email=settings.SUPER_USER_EMAIL,
                         password=settings.SUPER_USER_PASSWORD,
                         admin=True,
                         super_user=True)

                # optionally add super user apikey
                if getattr(settings, 'SUPER_USER_APIKEY', None):
                    u.apikey = settings.SUPER_USER_APIKEY
            else:
                log.warning('Updating super user "{}"\n'.format(
                    settings.SUPER_USER_EMAIL), line=False)
                u.name = settings.SUPER_USER,
                u.email = settings.SUPER_USER_EMAIL,
                u.password = settings.SUPER_USER_PASSWORD,
                u.admin = True
                super_user = True
            db.session.add(u)

            log.info('(Re)Loading SQL Extensions\n', line=False)
            # load sql extensions + functions
            for sql in load_sql():
                db.session.execute(sql)

            # load built-in sous-chefs
            for sc in load_sous_chefs():
                sc = sous_chef_schema.validate(sc)

                sc_obj = db.session.query(SousChef).filter_by(
                    slug=sc['slug']).first()
                if not sc_obj:
                    log.info(
                        'Importing Sous Chef "{}"\n'.format(sc['slug']), line=False)
                    sc_obj = SousChef(**sc)

                else:
                    log.warning(
                        'Updating Sous Chef "{}"\n'.format(sc['slug']), line=False)
                    sc = sous_chef_schema.update(sc_obj.to_dict(), sc)
                    # udpate
                    for name, value in sc.items():
                        setattr(sc_obj, name, value)
                db.session.add(sc_obj)

            # commit
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
