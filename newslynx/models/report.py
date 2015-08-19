from sqlalchemy.dialects.postgresql import JSON

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.text import slug


class Report(db.Model):

    __tablename__ = 'reports'
    __module__ = 'newslynx.models.report'
    
    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), index=True)
    name = db.Column(db.Text, index=True)
    slug = db.Column(db.Text, index=True)
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)
    data = db.Column(JSON)

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.template_id = kw.get('template_id')
        self.name = kw.get('name')
        self.slug = kw.get('slug', slug(kw.get('name')))
        self.data = kw.get('data', {})

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'template_id': self.template_id,
            'name': self.name,
            'slug': self.slug,
            'created': self.created,
            'updated': self.updated,
            'has_template': self.has_template,
            'data': self.data
        }

    def filename(self, format):
        """
        Create a filename for a report.
        """
        return "{}-{}.{}".format(self.slug, 
            self.created.strftime('%Y-%m-%d-%H-%m-%s'), format)

    @property 
    def has_template(self):
        return self.template_id is not None
    
    def render(self):
        return self.template.render(**self.to_dict())

    def __repr__(self):
        return "<Report %r / %r >" % (self.org_id, self.slug)
