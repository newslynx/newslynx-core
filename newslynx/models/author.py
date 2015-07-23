from sqlalchemy_utils.types import TSVectorType

from newslynx.core import db, SearchQuery
from newslynx.lib import dates


class Author(db.Model):

    """
    An author of a content-item.
    A unique author is a combination of an org_id and a name.
    """

    __tablename__ = 'authors'
    __module__ = 'newslynx.models.author'
    query_class = SearchQuery

    # the ID is the global bitly hash.
    id = db.Column(db.Integer, unique=True, primary_key=True, index=True)
    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)
    name = db.Column(db.Text, index=True)
    img_url = db.Column(db.Text)
    created = db.Column(db.DateTime(timezone=True), default=dates.now)
    updated = db.Column(db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    __table_args__ = (
        db.UniqueConstraint('org_id', 'name'),
    )

    # our search vector
    search_vector = db.Column(TSVectorType('name'))

    def __init__(self, **kw):
        self.org_id = kw.get('org_id')
        self.name = kw.get('name').upper()
        self.img_url = kw.get('img_url')

    def fetch_content_items(self):
        return self.content_items\
            .order_by("content.created desc")\
            .all()

    @property
    def content_item_ids(self):
        return [c.id for c in self.content_items]

    def simple_content(self, **kw):
        incl_metrics = kw.get('incl_metrics', False)
        output = []
        for c in self.fetch_content_items():
            d = {
                'id': c.id,
                'title': c.title,
                'description': c.description,
                'created': c.created,
                'img_url': c.img_url
            }
            if incl_metrics:
                d['metrics'] = c.summary_metric.metrics
            output.append(d)
        return output

    def to_dict(self, **kw):
        incl_content = kw.get('incl_content', False)
        d = {
            'id': self.id,
            'org_id': self.org_id,
            'name': self.name.title(),
            'img_url': self.img_url,
            'created': self.created,
            'updated': self.updated,
        }
        if incl_content:
            d['content_items'] = self.simple_content(**kw)
        return d

    def __repr__(self):
        return '<Author %r >' % (self.name)
