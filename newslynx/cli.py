#!/usr/bin/env python
import logging
import pkg_resources
import sys

from flask.ext.script import Manager
from flask.ext.migrate import MigrateCommand

from newslynx.views import app
from newslynx.core import db_session, db, rds
from newslynx.models import User, SousChef
from newslynx.init import load_sous_chefs
from newslynx.lib.serialize import obj_to_json
from newslynx import settings
from newslynx.dev import random_data
from newslynx.init import load_sql
from newslynx.constants import TASK_QUEUE_NAMES
from rq import Worker, Queue, Connection

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
def init():

    # create the database
    db.configure_mappers()
    db.create_all()

    # load sql extensions + functions
    for sql in load_sql():
        db_session.execute(sql)
    db_session.commit()


@manager.command
def gen_random_data():

    # create the database
    db.configure_mappers()
    db.create_all()

    # generate random data
    random_data.run()


@manager.option('-q', '--queue',
                help='The queue the worker should listen to. '
                     'Choose from {}'.format(", ".join(TASK_QUEUE_NAMES)))
def worker(queue):
    """
    start a worker on a queue.
    """
    if queue not in TASK_QUEUE_NAMES:
        raise ValueError('queue must be one of {}'.format(", ".join(TASK_QUEUE_NAMES)))
    with Connection(rds):
        worker = Worker(Queue(queue))
        worker.work()


def run():
    manager.run()

if __name__ == '__main__':
    run()
