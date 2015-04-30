import copy

from newslynx.core import db
from newslynx.lib.serialize import json_to_obj, obj_to_json


class Setting(db.Model):

    __tablename__ = 'org_settings'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), index=True)
    name = db.Column(db.Text, index=True)
    value = db.Column(db.Text)
    json_value = db.Column(db.Boolean)

    def __init__(self, **kw):
        self.organization_id = kw.get('organization_id')
        self.name = kw.get('name')
        self.json_value = kw.get('json_value', False)
        if self.json_value:
            v = kw.get('value')
            if not isinstance(v, basestring):
                v = obj_to_json(v)
            self.value = v
        else:
            v = str(kw.get('value'))
            assert isinstance(v, basestring)
            self.value = v

    def to_dict(self):
        v = copy.copy(self.value)
        if self.json_value:
            v = json_to_obj(v)

        return {
            'id': self.id,
            'name': self.name,
            'value': v
        }

    def __repr__(self):
        return "<Setting %r / %r >" % (self.name, self.value)
