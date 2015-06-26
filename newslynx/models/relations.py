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
    return db.Table(
        name,
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

# events <=> tags
events_tags = join_table('events_tags', 'event', 'tag')

# content_items <=> authors.
content_items_authors = db.Table(
    'content_items_authors',
    db.Column(
        'author_id',
        db.Integer,
        db.ForeignKey(
            'authors.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True),
    db.Column(
        'content_item_id',
        db.Integer,
        db.ForeignKey(
            'content.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True)
    )

# content_items <=> events
content_items_events = db.Table(
    'content_items_events',
    db.Column(
        'event_id',
        db.Integer,
        db.ForeignKey(
            'events.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True),
    db.Column(
        'content_item_id',
        db.Integer,
        db.ForeignKey(
            'content.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True)
)

# content_items <=> tags
content_items_tags = db.Table(
    'content_items_tags',
    db.Column(
        'tag_id',
        db.Integer,
        db.ForeignKey(
            'tags.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True),
    db.Column(
        'content_item_id',
        db.Integer,
        db.ForeignKey(
            'content.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True)
)


# # content_items <=> content_items.
# content_items_content_items = db.Table(
#     'content_items_content_items',
#     db.Column(
#         'from_content_item_id',
#         db.Integer,
#         db.ForeignKey('content.id', onupdate='CASCADE'),
#         primary_key=True),
#     db.Column(
#         'to_content_item_id',
#         db.Integer,
#         db.ForeignKey('content.id', onupdate='CASCADE'),
#         primary_key=True)
# )
