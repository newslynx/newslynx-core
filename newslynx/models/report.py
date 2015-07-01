from sqlalchemy.dialects.postgresql import JSON
import os 

from jinja2 import Template
from slugify import slugify

from newslynx.core import db
from newslynx.lib import dates
from newslynx.lib.pkg import pandoc

from tempfile import NamedTemporaryFile

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
        self.slug = kw.get('slug', slugify(kw.get('name')))
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
            'has_template': self.template_id is not None,
            'data': self.data
        }
    
    def render(self, format):
        contents = self.template.render(data=self.data)
        if self.template.format == 'html':
            return contents, 'application/html'
        p = pandoc.Document()
        p.markdown = contents 
        if format == "html":
            return p.html
        
        elif format == "pdf":
            tempfile = NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False)
            output_file = p.to_file(tempfile.name)
            if not output_file:
                return None
            contents = open(output_file).read()
            try:
                os.remove(output_file)
                os.remove(tempfile.name)
            except OSError:
                pass
            return contents




    def __repr__(self):
        return "<Report %r / %r >" % (self.org_id, self.slug)
