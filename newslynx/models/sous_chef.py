from collections import OrderedDict
from sqlalchemy.dialects.postgresql import JSON, ENUM, ARRAY

from newslynx.core import db
from newslynx.lib.text import slug
from newslynx.constants import SOUS_CHEF_CREATES


class SousChef(db.Model):

    __tablename__ = 'sous_chefs'
    __module__ = 'newslynx.models.sous_chef'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    name = db.Column(db.Text, index=True, unique=True)
    slug = db.Column(db.Text, index=True, unique=True)
    description = db.Column(db.Text)
    runs = db.Column(db.Text)
    filepath = db.Column(db.Text)
    is_command = db.Column(db.Boolean)
    creates = db.Column(
        ENUM(*SOUS_CHEF_CREATES, name='sous_chef_creates_enum'), index=True)
    option_order = db.Column(ARRAY(db.Text))
    requires_auths = db.Column(ARRAY(db.Text))
    requires_settings = db.Column(ARRAY(db.Text))
    options = db.Column(JSON)
    metrics = db.Column(JSON)

    def __init__(self, **kw):

        # set columns
        self.org_id = kw.get('org_id')
        self.name = kw.get('name')
        self.slug = slug(kw.get('slug', kw['name']))
        self.description = kw.get('description')
        self.runs = kw.get('runs')
        self.filepath = kw.get('filepath')
        self.is_command = kw.get('is_command')
        if self.is_command:
            self.filepath = kw.get('runs')
        self.creates = kw.get('creates', 'null')
        if not self.creates:
            self.creates = 'null'
        self.required_auths = kw.get('requires_auths', [])
        self.required_settings = kw.get('requires_settings', [])
        self.option_order = kw.get('option_order', [])
        self.options = kw.get('options', {})
        self.metrics = kw.get('metrics', {})

    def to_dict(self, **kw):
        incl_options = kw.get('incl_options', True)

        d = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'filepath': self.filepath,
            'description': self.description,
            'runs': self.runs,
            'is_command': self.is_command,
            'creates': self.creates,
            'requires_auths': self.requires_auths,
            'requires_settings': self.requires_settings
        }
        if incl_options:
            d['options'] = self.ordered_options
            d['option_order'] = self.option_order
        if self.creates:
            if 'metrics' in self.creates:
                d['metrics'] = self.metrics
        return d

    @property
    def config(self, **kw):
        """
        The original configuration representation.
        """
        return {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'runs': self.runs,
            'creates': self.creates,
            'requires_auths': self.requires_auths,
            'requires_settings': self.requires_settings,
            'option_order': self.option_order,
            'options': self.options,
            'metrics': self.metrics,
        }

    @property
    def ordered_options(self):
        """
        Optionally order by specific keys.
        """
        if len(self.option_order):
            sort_order = {
                k: i for i, k in enumerate(self.option_order)
            }
            return OrderedDict(sorted(self.options.items(), key=lambda k: sort_order.get(k[0], None)))
        return self.options

    def __repr__(self):
        return '<SousChef %r >' % (self.slug)
