from sqlalchemy.dialects.postgresql import JSON, ENUM

from newslynx.core import db
from newslynx.lib import dates


class Recipe(db.Model):

    __tablename__ = 'recipes'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    task_id = db.Column(
        db.Integer, db.ForeignKey('tasks.id'), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), index=True)
    name = db.Column(db.Text)
    description = db.Column(db.Text)
    config = db.Column(JSON)
    created = db.Column(db.DateTime(timezone=True), index=True)
    updated = db.Column(db.DateTime(timezone=True), index=True)
    status = db.Column(
        ENUM('running', 'stable', 'error', name='recipe_status_enum'), index=True)
    scheduled = db.Column(db.Boolean)
    interval = db.Column(db.Integer)
    backoff = db.Column(db.Float)
    ttl = db.Column(db.Integer)

    # relations
    events = db.relationship(
        'Event', backref=db.backref('recipe', lazy='joined'), lazy='dynamic')

    # relations
    things = db.relationship(
        'Thing', backref=db.backref('recipe', lazy='joined'), lazy='dynamic')

    # relations
    metrics = db.relationship(
        'Metric', backref=db.backref('recipe', lazy='joined'), lazy='dynamic')

    task = db.relationship(
        'Task', backref=db.backref('recipes', lazy='joined'), lazy='joined')

    def __init__(self, **kw):
        self.task_id = kw.get('task_id')
        self.user_id = kw.get('user_id')
        self.organization_id = kw.get('organization_id')
        self.name = kw.get('name')
        self.description = kw.get('description')
        self.config = kw.get('config', {})
        self.created = kw.get('created', dates.now())
        self.updated = kw.get('updated', dates.now())
        self.status = kw.get('status', 'stable')
        self.scheduled = kw.get('scheduled', True)
        self.interval = kw.get('interval', 3600)
        self.backoff = kw.get('backoff', 1)
        self.ttl = kw.get('ttl', None)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task.name,
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'name': self.name,
            'description': self.description,
            'config': self.config,
            'status': self.status,
            'created': self.created,
            'scheduled': self.scheduled,
            'interval': self.interval,
            'backoff': self.backoff,
            'ttl': self.ttl
        }

    def __repr__(self):
        return '<Recipe %r >' % (self.name)
