from newslynx.core import db


class ThingThing(db.Model):

    """
    A relationship of a thing to another thing (ie a link)
    """
    __tablename__ = 'things_things'

    id = db.Column(db.Integer, unique=True, primary_key=True, index=True)
    from_thing_id = db.Column(
        db.Integer, db.ForeignKey('things.id'), index=True)
    to_thing_id = db.Column(db.Integer, db.ForeignKey('things.id'), index=True)
    # whether this is an external link.
    external = db.Column(db.Boolean, index=True)

    def __init__(self, from_thing_id, to_thing_id, **kw):
        self.from_thing_id = from_thing_id
        self.to_thing_id = to_thing_id
        self.external = kw.get('external', True)

    def get_id(self):
        return self.id


# join table utils.
def join_table(name, a, b):
    """
    Convenience method for building a join table.
    Args:
        | name (str)    -- name to give the table
        | a (str)       -- name of the first table being joined
        | b (str)       -- name of the second table being joined
    Example::
        stories_events = join_table('stories_events', 'story', 'event')
    """
    return db.Table(name,
                    db.Column('{0}_id'.format(a),
                              db.Integer,
                              db.ForeignKey(
                                  '{0}s.id'.format(a), ondelete='CASCADE', onupdate='CASCADE'),
                              primary_key=True),
                    db.Column('{0}_id'.format(b),
                              db.Integer,
                              db.ForeignKey(
                                  '{0}s.id'.format(b), ondelete='CASCADE', onupdate='CASCADE'),
                              primary_key=True))


# users <=> organizations.
organizations_users = join_table('organizations_users', 'organization', 'user')

# things <=> events
things_events = join_table('things_events', 'thing', 'event')

# things <=> tags
things_tags = join_table('things_tags', 'thing', 'tag')

# events <=> tags
events_tags = join_table('events_tags', 'event', 'tag')

# things <=> creators.
things_creators = join_table('things_creators', 'thing', 'creator')
