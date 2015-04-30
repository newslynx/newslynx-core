from sqlalchemy.dialects.postgresql import JSON

from newslynx.core import db


class Auth(db.Model):

    __tablename__ = 'authorizations'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), index=True)
    name = db.Column(db.Text, index=True)
    value = db.Column(JSON)

    def __init__(self, **kw):
        self.organization_id = kw.get('organization_id')
        self.name = kw.get('name')
        self.value = kw.get('value')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value
        }

    def __repr__(self):
        return "<Auth %r / %r >" % (self.organization_id, self.name)
