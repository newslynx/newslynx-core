from sqlalchemy import func, desc

from newslynx.models import Event, Recipe, Tag, SousChef, Thing
from newslynx.models.relations import events_tags, things_tags
from newslynx.core import db


def events_by_recipes(event_ids):
    """
    Count the number of events associated with recipes.
    """
    recipe_counts = db.session\
        .query(Event.recipe_id, func.count(Recipe.id))\
        .join(Recipe)\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(Recipe.id)))\
        .group_by(Event.recipe_id, Recipe.slug)\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'count'], r)) for r in recipe_counts]


def events_by_tags(event_ids):
    """
    Count the number of events associated with tags.
    """
    tag_counts = db.session\
        .query(Tag.id, func.count(Tag.id))\
        .outerjoin(events_tags)\
        .filter(events_tags.c.event_id.in_(event_ids))\
        .order_by(desc(func.count(Tag.id)))\
        .group_by(Tag.id)\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'count'], c))
            for c in tag_counts]


def events_by_categories(event_ids):
    """
    Count the number of events associated with tag categories.
    """
    category_counts = db.session\
        .query(Tag.category, func.count(Tag.category))\
        .outerjoin(events_tags)\
        .filter(events_tags.c.event_id.in_(event_ids))\
        .order_by(desc(func.count(Tag.category)))\
        .group_by(Tag.category).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['category', 'count'], c)) for c in category_counts]


def events_by_levels(event_ids):
    """
    Count the number of events associated with tag levels.
    """
    level_counts = db.session\
        .query(Tag.level, func.count(Tag.level))\
        .outerjoin(events_tags)\
        .filter(events_tags.c.event_id.in_(event_ids))\
        .order_by(desc(func.count(Tag.level)))\
        .group_by(Tag.level).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['level', 'count'], c)) for c in level_counts]


def events_by_sous_chefs(event_ids):
    """
    Count the number of events associated with sous chefs.
    """
    sous_chef_counts = db.session\
        .query(SousChef.id, func.count(SousChef.slug))\
        .join(Recipe)\
        .join(Event)\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(SousChef.slug)))\
        .group_by(SousChef.id).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'count'], c)) for c in sous_chef_counts]


def events_by_things(event_ids):
    """
    Count the number of events associated with things.
    """
    thing_counts = db.session\
        .query(Thing.id, Thing.title, func.count(Thing.id))\
        .filter(Thing.events.any(Event.id.in_(event_ids)))\
        .order_by(desc(func.count(Thing.id)))\
        .group_by(Thing.id, Thing.url, Thing.title).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'title', 'count'], c)) for c in thing_counts]


def events_by_statuses(event_ids):
    """
    Count the number of events associated with event statuses.
    """
    status_counts = db.session\
        .query(Event.status, func.count(Event.status))\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(Event.status)))\
        .group_by(Event.status).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['status', 'count'], c)) for c in status_counts]


def events_by_provenances(event_ids):
    """
    Count the number of events that have been created manually
    or not.
    """
    status_counts = db.session\
        .query(Event.provenance, func.count(Event.provenance))\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(Event.provenance)))\
        .group_by(Event.provenance).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['provenance', 'count'], c)) for c in status_counts]


def events(by, event_ids):
    """
    Simplified mapping of facet functions
    """
    fx_lookup = {
        'recipes': events_by_recipes,
        'tags': events_by_tags,
        'categories': events_by_categories,
        'levels': events_by_levels,
        'sous_chefs': events_by_sous_chefs,
        'things': events_by_things,
        'statuses': events_by_statuses,
        'provenances': events_by_provenances
    }
    return fx_lookup.get(by)(event_ids)


# things

def things_by_types(thing_ids):
    """
    Count the number of things associated with thing types.
    """
    type_counts = db.session\
        .query(Thing.type, func.count(Thing.type))\
        .filter(Thing.id.in_(thing_ids))\
        .group_by(Thing.type)\
        .order_by(desc(func.count(Thing.type)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['type', 'count'], r)) for r in type_counts]


def things_by_provenances(thing_ids):
    """
    Count the number of things associated with thing types.
    """
    type_counts = db.session\
        .query(Thing.provenance, func.count(Thing.provenance))\
        .filter(Thing.id.in_(thing_ids))\
        .group_by(Thing.provenance)\
        .order_by(desc(func.count(Thing.provenance)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['provenance', 'count'], r)) for r in type_counts]


def things_by_domains(thing_ids):
    """
    Count the number of things associated with domains.
    """
    domain_counts = db.session\
        .query(Thing.domain, func.count(Thing.domain))\
        .filter(Thing.id.in_(thing_ids))\
        .group_by(Thing.domain)\
        .order_by(desc(func.count(Thing.domain)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['domain', 'count'], r)) for r in domain_counts]


def things_by_recipes(thing_ids):
    """
    Count the number of things associated with recipes.
    """
    recipe_counts = db.session\
        .query(Recipe.slug, func.count(Recipe.slug))\
        .join(Thing)\
        .filter(Thing.id.in_(thing_ids))\
        .order_by(desc(func.count(Recipe.slug)))\
        .group_by(Recipe.slug).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['slug', 'count'], r)) for r in recipe_counts]


def things_by_tags(thing_ids):
    """
    Count the number of things associated with tags.
    """
    tag_counts = db.session\
        .query(things_tags.c.tag_id, func.count(things_tags.c.tag_id))\
        .filter(things_tags.c.thing_id.in_(thing_ids))\
        .group_by(things_tags.c.tag_id)\
        .order_by(desc(func.count(things_tags.c.tag_id)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'count'], c)) for c in tag_counts]


def things_by_sous_chefs(thing_ids):
    """
    Count the number of things associated with sous chefs.
    """
    task_counts = db.session\
        .query(SousChef.slug, func.count(SousChef.slug))\
        .outerjoin(Recipe)\
        .outerjoin(Thing)\
        .filter(Thing.id.in_(thing_ids))\
        .order_by(desc(func.count(SousChef.slug)))\
        .group_by(SousChef.slug).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['slug', 'count'], c)) for c in task_counts]


def things(by, thing_ids):
    """
    Simplified mapping of facet functions
    """
    fx_lookup = {
        'recipes': things_by_recipes,
        'tags': things_by_tags,
        'sous_chefs': things_by_sous_chefs,
        'statuses': things_by_types,
        'types': things_by_types,
        'domains': things_by_domains,
        'provenances': things_by_provenances
    }
    return fx_lookup.get(by)(thing_ids)
