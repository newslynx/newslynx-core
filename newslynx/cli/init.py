import sys
import os
from inspect import isgenerator

import click
from colorama import Fore
import argparse

from newslynx.cli.common import echo, echo_error, load_data
from newslynx.client import API
from newslynx.lib import serialize
from newslynx.init import load_sous_chefs
from newslynx.models import sous_chef_schema
from newslynx.init import load_sql
from newslynx.models import User, SousChef
from newslynx.views import app
from newslynx.core import db_session, db
from newslynx import settings

def setup(parser):
    """
    Install this parser. Basic for now.
    """
    init_parser = parser.add_parser("init", help="Initializes the database, super user, and core sous chefs.")
    return 'init', run

def run(opts, **kwargs):
    # create the database
    try:
        with app.app_context():
            echo('Creating database "{}"'.format(settings.SQLALCHEMY_DATABASE_URI), 
                no_color=opts.no_color)
            db.configure_mappers()
            db.create_all()
            
            # create the super user
            u = User.query.filter_by(email=settings.SUPER_USER_EMAIL).first()
            if not u:
                echo('Creating super user "{}"'.format(settings.SUPER_USER_EMAIL),
                    no_color=opts.no_color)
                u = User(name=settings.SUPER_USER,
                         email=settings.SUPER_USER_EMAIL,
                         password=settings.SUPER_USER_PASSWORD,
                         admin=True,
                         super_user=True)

                # optionally add super user apikey
                if getattr(settings, 'SUPER_USER_APIKEY', None):
                    u.apikey = settings.SUPER_USER_APIKEY
            else:
                echo('Updating super user "{}"'.format(settings.SUPER_USER_EMAIL), 
                    no_color=opts.no_color)
                u.name=settings.SUPER_USER,
                u.email=settings.SUPER_USER_EMAIL,
                u.password=settings.SUPER_USER_PASSWORD,
                u.admin=True
                super_user=True
            db.session.add(u)

            echo('(Re)Loading SQL Extensions', no_color=opts.no_color)
            # load sql extensions + functions
            for sql in load_sql():
                db.session.execute(sql)

            # load built-in sous-chefs
            for sc in load_sous_chefs():
                sc = sous_chef_schema.validate(sc)

                sc_obj = db.session.query(SousChef).filter_by(slug=sc['slug']).first()
                if not sc_obj:
                    echo('Importing Sous Chef "{}"'.format(sc['slug']),
                        no_color=opts.no_color)
                    sc_obj = SousChef(**sc)
                
                else:
                    echo('Updating Sous Chef "{}"'.format(sc['slug']),
                        no_color=opts.no_color)
                    sc = sous_chef_schema.update(sc_obj.to_dict(), sc)
                    # udpate
                    for name, value in sc.items():
                        setattr(sc_obj, name, value)
                db.session.add(sc_obj)

            # commit
            db.session.commit()
            db.session.close()

    except Exception as e:
        db.session.rollback()
        db.session.close()
        raise e
