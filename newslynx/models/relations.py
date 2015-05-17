from newslynx.core import db


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


# users <=> orgs.
orgs_users = join_table('orgs_users', 'org', 'user')

# things <=> events
things_events = join_table('things_events', 'thing', 'event')

# things <=> tags
things_tags = join_table('things_tags', 'thing', 'tag')

# events <=> tags
events_tags = join_table('events_tags', 'event', 'tag')

# things <=> creators.
things_creators = join_table('things_creators', 'thing', 'creator')
