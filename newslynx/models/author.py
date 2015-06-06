from sqlalchemy_utils.types import TSVectorType

from newslynx.core import db
from newslynx.lib import dates


class Author(db.Model):

    """
    An author of a content-item.
    A unique author is a combination of an org_id and a name.
    """

    __tablename__ = 'authors'

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

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'name': self.name.title(),
            'img_url': self.img_url,
            'created': self.created,
            'updated': self.updated
        }

    def __repr__(self):
        return '<Author %r >' % (self.name)
