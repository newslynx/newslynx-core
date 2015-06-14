from slugify import slugify
from sqlalchemy.dialects.postgresql import JSON, ENUM

from newslynx.core import db
from newslynx.constants import SOUS_CHEF_CREATES


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
