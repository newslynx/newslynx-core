import copy

from newslynx.core import db
from newslynx.lib.serialize import json_to_obj, obj_to_json


class Setting(db.Model):

    __tablename__ = 'org_settings'
    __module__ = 'newslynx.models.setting'
    
    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    name = db.Column(db.Text, index=True)
    value = db.Column(db.Text)
    json_value = db.Column(db.Boolean)

    __table_args__ = (
        db.UniqueConstraint('org_id', 'name'),
    )

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.name = kw.get('name')
        self.json_value = kw.get('json_value', False)
        if self.json_value:
            v = kw.get('value')
            if not isinstance(v, basestring):
                v = obj_to_json(v)
            self.value = v
        else:
            self.value = str(kw.get('value'))

    def to_dict(self):
        v = copy.copy(self.value)
        if self.json_value:
            v = json_to_obj(v)

        return {
            'id': self.id,
            'org_id': self.org_id,
            'name': self.name,
            'value': v,
            'json_value': self.json_value
        }

    def __repr__(self):
        return "<Setting %r / %r >" % (self.name, self.value)
