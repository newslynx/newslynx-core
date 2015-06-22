from slugify import slugify
from collections import OrderedDict
from sqlalchemy.dialects.postgresql import JSON, ENUM, ARRAY

from newslynx.core import db
from newslynx.constants import SOUS_CHEF_CREATES


class SousChef(db.Model):

    __tablename__ = 'sous_chefs'
    __module__ = 'newslynx.models.sous_chef'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    name = db.Column(db.Text, index=True, unique=True)
    slug = db.Column(db.Text, index=True, unique=True)
    description = db.Column(db.Text)
    runs = db.Column(db.Text)
    is_command = db.Column(db.Boolean)
    creates = db.Column(
        ENUM(*SOUS_CHEF_CREATES, name='sous_chef_creates_enum'), index=True)
    option_order = db.Column(ARRAY(db.Text))
    options = db.Column(JSON)
    metrics = db.Column(JSON)

    def __init__(self, **kw):

        # set columns
        self.name = kw.get('name')
        self.slug = slugify(kw.get('slug', kw['name']))
        self.description = kw.get('description')
        self.runs = kw.get('runs')
        self.is_command = kw.get('is_command')
        self.creates = kw.get('creates')
        self.option_order = kw.get('option_order', [])
        self.options = kw.get('options', {})
        self.metrics = kw.get('metrics', {})

    def to_dict(self, **kw):
        incl_options = kw.get('incl_options', True)

        d = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'runs': self.runs,
            'is_command': self.is_command,
            'option_order': self.option_order,
            'creates': self.creates
        }
        if incl_options:
            d['options'] = self.ordered_options
        if 'metrics' in self.creates:
            d['metrics'] = self.metrics
        return d

    @property
    def ordered_options(self):
        """
        Optionally order by specific keys.
        """
        if len(self.option_order):
            sort_order = {k: i for i, k in enumerate(self.option_order)}
            return OrderedDict(sorted(self.options.items(), key=lambda k: sort_order.get(k[0], None)))
        return self.options

    def __repr__(self):
        return '<SousChef %r >' % (self.slug)
