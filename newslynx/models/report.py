from sqlalchemy.dialects.postgresql import JSON

from newslynx.core import db
from newslynx.lib import dates


class Report(db.Model):

    __tablename__ = 'reports'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    name = db.Column(db.Text, index=True)
    created = db.Column(db.DateTime(timezone=True), index=True)
    schema = db.Column(JSON) # dynamically generated.
    value = db.Column(JSON)

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.name = kw.get('name')
        self.created = kw.get('created', dates.now())
        self.schema = kw.get('schema')
        self.value = kw.get('value')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created': self.created,
            'schema': self.schema,
            'value': self.value
        }

    def __repr__(self):
        return "<Report %r / %r >" % (self.org_id, self.name)
