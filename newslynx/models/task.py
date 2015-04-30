from sqlalchemy.dialects.postgresql import JSON

from newslynx.core import db
from newslynx.lib import dates


class Task(db.Model):

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    name = db.Column(db.Text)
    description = db.Column(db.Text)
    created = db.Column(db.DateTime(timezone=True))
    config = db.Column(JSON)


    def __init__(self, **kw):
        self.name = kw.get('name')
        self.description = kw.get('description')
        self.created = kw.get('created', dates.now())
        self.config = kw.get('config', {})

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created': self.created,
            'config': self.config,
            'recipes': self.recipes
        }

    def __repr__(self):
        return '<Task %r >' % (self.name)
