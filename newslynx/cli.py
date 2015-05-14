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
from newslynx.lib.serialize import obj_to_json
from newslynx import settings
from newslynx.tests import random_data

log = logging.getLogger('newslynx')

manager = Manager(app)
manager.add_command('migrate', MigrateCommand)


@manager.command
def version():
    print pkg_resources.get_distribution("newslynx").version


@manager.command
def config():
    sys.stderr.write('Newslynx Configurations:\n')
    for name, value in settings.config.items():
        sys.stderr.write("{}: {}\n".format(name, value))


@manager.command
def db_drop():
    db.drop_all()


@manager.command
def init():
    # create the database
    db.configure_mappers()
    db.create_all()


@manager.command
def gen_random_data():
    # create the database
    db.configure_mappers()
    db.create_all()
    random_data.run()


@manager.command
def refresh_sous_chefs():
    for sc in load_sous_chefs():
        s = db_session.query(SousChef).filter_by(slug=sc['slug'])
        if not s:
            s = SousChef(**sc)
            db_session.add(s)
    db_session.commit()


@manager.command
def reinit():
    db_drop()
    init()


@manager.command
def create_admin_user(email, password, name, admin=False):
    u = db_session.query(User).filter_by(email=settings.ADMIN_EMAIL).first()
    if not u:
        u = User(email=email,
                 password=password,
                 name=name,
                 admin=admin)

        db_session.add(u)
        db_session.commit()
    sys.stderr.write('New User:')
    sys.stdout.write(obj_to_json(u) + "\n")


def run():
    manager.run()


if __name__ == '__main__':
    run()
