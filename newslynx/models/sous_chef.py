import os
import importlib

from jsonschema import Draft4Validator
from slugify import slugify
from sqlalchemy.dialects.postgresql import JSON, ENUM

from newslynx.core import db
from newslynx.sc import SousChef as SC
from newslynx.constants import SOUS_CHEF_CREATES
from newslynx.exc import SousChefSchemaError
from newslynx.lib.serialize import yaml_to_obj
from newslynx.util import here, update_nested_dict


# load souschef schema + validator.
SOUS_CHEF_JSON_SCHEMA = yaml_to_obj(
    open(here(__file__, 'sous_chef.yaml')).read())

# these are default options that all sous chefs have.
DEFAULT_SOUS_CHEF_OPTIONS = yaml_to_obj(
    open(here(__file__, 'sous_chef_defaults.yaml')).read())

# a json-schema validator for a sous chef.
SOUS_CHEF_VALIDATOR = Draft4Validator(SOUS_CHEF_JSON_SCHEMA)


def validate_python_sous_chef(sc):
    """
    Check if a python sous_chef is a valid import.
    """
    try:

        import_parts = sc['runs'].split('.')
        module = '.'.join(import_parts[:-1])
        c = import_parts[-1]
        m = importlib.import_module(module)
        sous_chef = getattr(m, c, None)

        if not sous_chef:
            raise SousChefSchemaError(
                '{} does not exist in module {}.'.format(m, c)
            )

    except ImportError:
        raise SousChefSchemaError(
            '{} is not importable'.format(module))

    if not issubclass(sous_chef, SC):
        raise SousChefSchemaError(
            '{} does not inherit from newslynx.sc.SousChef.'
            .format(sc['runs']))


def validate_command_sous_chef(sc):
    """
    Check if a executable sous_chef is valid.
    """
    sc['is_command'] = True
    if not sc['runs'].startswith('/'):
        raise SousChefSchemaError(
            '{} does not have an absolute path.'.format(sc['runs']))

    if not os.path.exists(sc['runs']):
        raise SousChefSchemaError(
            '{} does not exist.'.format(sc['runs']))

    if not os.access(sc['runs'], os.X_OK):
        raise SousChefSchemaError(
            '{} is not an executable.'.format(sc['runs']))


def validate_sous_chef_json_schema(sc):
    """
    Check if a sous chef follows the core JSON schema.
    """
    schema_errors = sorted(
        SOUS_CHEF_VALIDATOR.iter_errors(sc), key=lambda e: e.path)

    if len(schema_errors):
        message = "This SousChef config is invalid. Here are the errors:"
        for error in schema_errors:
            message += "\n{} - {}".format(error.path, error.message)
        raise SousChefSchemaError(message)


def validate_sous_chef(sc):
    """
    Validate a sous chef schema:
    First chef against the canoncial json schema.
    Then check if the `runs` field is a valid python
    module or an executable script that exists where
    it has been declared. Then merge the default
    sous-chef options with the provied ones.
    """

    # check the json schema
    validate_sous_chef_json_schema(sc)

    # check if `runs` is a python module that inherits from
    # newslynx.sc.SousChef
    if not '/' in sc['runs']:
        sc['is_command'] = False
        validate_python_sous_chef(sc)

    # otherwise validate the command
    else:
        validate_command_sous_chef(sc)

    # if everything is kosher, merge the sous-chef options
    # with the defaults
    sc['options'] = update_nested_dict(
        sc['options'], DEFAULT_SOUS_CHEF_OPTIONS)
    return sc


class SousChef(db.Model):

    __tablename__ = 'sous_chefs'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    name = db.Column(db.Text, index=True, unique=True)
    slug = db.Column(db.Text, index=True, unique=True)
    description = db.Column(db.Text)
    runs = db.Column(db.Text)
    is_command = db.Column(db.Boolean)
    creates = db.Column(
        ENUM(*SOUS_CHEF_CREATES, name='sous_chef_creates_enum'), index=True)
    options = db.Column(JSON)

    def __init__(self, **kw):

        # validate the sous chef
        kw = validate_sous_chef(kw)

        # set columns
        self.name = kw.get('name')
        self.slug = slugify(kw.get('slug', kw['name']))
        self.description = kw.get('description')
        self.runs = kw.get('runs')
        self.is_command = kw.get('is_command')
        self.creates = kw.get('creates')
        self.options = kw.get('options', {})

    def to_dict(self, incl_options=True):
        d = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'runs': self.runs,
            'is_command': self.is_command,
            'creates': self.creates
        }
        if incl_options:
            d['options'] = self.options
        return d

    def __repr__(self):
        return '<SousChef %r >' % (self.slug)
