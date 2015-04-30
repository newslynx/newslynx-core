from sqlalchemy_utils.types import TSVectorType

from newslynx.core import db
from newslynx.lib import dates


class Creator(db.Model):

    """
    A creator is an author of a thing.
    A unique creator is a combination of an organization_id and a name.
    """

    __tablename__ = 'creators'

    # the ID is the global bitly hash.
    id = db.Column(db.Integer, unique=True, primary_key=True, index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), index=True, primary_key=True)
    name = db.Column(db.Text, index=True, primary_key=True)
    created = db.Column(db.DateTime(timezone=True), index=True)

    __table_args__ = (
        db.UniqueConstraint('organization_id', 'name'),
    )

    # our search vector
    search_vector = db.Column(TSVectorType('name'))

    def __init__(self, **kw):
        self.organization_id = kw.get('organization_id')
        self.name = kw.get('name').upper()
        self.created = kw.get('created', dates.now())

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'name': self.name,
            'created': self.created,
        }
    
    def __repr__(self):
        return '<Creator %r >' % (self.name)
