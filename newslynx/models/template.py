from sqlalchemy.dialects.postgresql import ENUM
from jinja2 import Template as Tmpl

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.text import slug
from newslynx.constants import TEMPLATE_FORMATS


class Template(db.Model):

    __tablename__ = 'templates'
    __module__ = 'newslynx.models.template'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    name = db.Column(db.Text)
    slug = db.Column(db.Text, index=True)
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)
    template = db.Column(db.Text)
    format = db.Column(ENUM(*TEMPLATE_FORMATS, name="template_format_enum"))

    reports = db.relationship(
        'Report',
        backref=db.backref('template', lazy='joined'),
        lazy='dynamic',
        cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('org_id', 'slug'),
    )

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.name = kw.get('name')
        self.slug = kw.get('slug', slug(kw.get('name')))
        self.template = kw.get('template')
        self.format = kw.get('format')
        self.data = kw.get('data')

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'name': self.name,
            'slug': self.slug,
            'created': self.created,
            'updated': self.updated,
            'template': self.template,
            'format': self.format
        }

    def render(self, **kw):
        """
        Render this template.
        """
        t = Tmpl(self.template)
        return t.render(**kw)

    def __repr__(self):
        return "<Template %r / %r >" % (self.org_id, self.slug)