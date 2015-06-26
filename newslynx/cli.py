#!/usr/bin/env python
import logging
import pkg_resources
import sys

from flask.ext.script import Manager
from flask.ext.migrate import MigrateCommand

from newslynx.views import app
from newslynx.core import db_session, db
from newslynx.models import User, SousChef
from newslynx.init import load_sous_chefs
from newslynx.models import sous_chef_schema
from newslynx.dev import random_data
from newslynx.init import load_sql
from newslynx import settings
from newslynx.models import URLCache, ExtractCache, ThumbnailCache
from newslynx.models import ComparisonsCache

log = logging.getLogger(__name__)


manager = Manager(app)
manager.add_command('migrate', MigrateCommand)


@manager.command
def version():
    print pkg_resources.get_distribution("newslynx").version


@manager.command
def config():
    sys.stderr.write('Newslynx Configurations:\n')
    for name, value in settings.CONFIG.items():
        sys.stderr.write("{}: {}\n".format(name, value))


@manager.command
def init():

    # create the database
    db.configure_mappers()
    db.create_all()

    # create the super user
    u = User(name=settings.SUPER_USER,
             email=settings.SUPER_USER_EMAIL,
             password=settings.SUPER_USER_PASSWORD,
             admin=True,
             super_user=True)

    # optionally add super user apikey
    if getattr(settings, 'SUPER_USER_APIKEY', None):
        u.apikey = settings.SUPER_USER_APIKEY
    db_session.add(u)

    # load sql extensions + functions
    for sql in load_sql():
        db_session.execute(sql)

    # load built-in sous-chefs
    for sc in load_sous_chefs():
        sc = sous_chef_schema.validate(sc)
        s = SousChef(**sc)
        db_session.add(s)

    # commit
    db_session.commit()


@manager.command
def gen_random_data():

    # create the database
    db.configure_mappers()
    db.create_all()

    # generate random data
    random_data.run()


@manager.command
def flush_comparison_cache():
    ComparisonsCache.flush()


@manager.command
def flush_work_cache():
    URLCache.flush()
    ExtractCache.flush()
    ThumbnailCache.flush()


def run():
    manager.run()
