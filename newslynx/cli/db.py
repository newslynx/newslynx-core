"""
Manage migrations with alembic.
"""


def setup(parser):

    db_parser = parser.add_parser(
        "db", help="Manage Database Migrations via alembic.")
    return 'db', run


def run(opts, **kw):
    from flask.ext.migrate import Migrate, MigrateCommand
    from flask.ext.script import Manager
    from newslynx.views import app
    from newslynx.core import db
    migrate = Migrate(app, db)
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    manager.run()
