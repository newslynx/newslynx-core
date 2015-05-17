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
    return [dict(zip(['id', 'count'], c))
            for c in tag_counts]


def events_by_tag_categories(event_ids):
    """
    Count the number of events associated with tag categories.
    """
    category_counts = db.session\
        .query(Tag.category, func.count(Tag.category))\
        .outerjoin(events_tags)\
        .filter(events_tags.c.event_id.in_(event_ids))\
        .order_by(desc(func.count(Tag.category)))\
        .group_by(Tag.category).all()
    return [dict(zip(['category', 'count'], c)) for c in category_counts]


def events_by_tag_levels(event_ids):
    """
    Count the number of events associated with tag levels.
    """
    level_counts = db.session\
        .query(Tag.level, func.count(Tag.level))\
        .outerjoin(events_tags)\
        .filter(events_tags.c.event_id.in_(event_ids))\
        .order_by(desc(func.count(Tag.level)))\
        .group_by(Tag.level).all()
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
        .group_by(SousChef.id)
    return [dict(zip(['id', 'count'], c)) for c in sous_chef_counts.all()]


def events_by_things(event_ids):
    """
    Count the number of events associated with things.
    """
    thing_counts = db.session\
        .query(Thing.id, Thing.title, func.count(Thing.id))\
        .filter(Thing.events.any(Event.id.in_(event_ids)))\
        .order_by(desc(func.count(Thing.id)))\
        .group_by(Thing.id, Thing.url, Thing.title).all()
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
    return [dict(zip(['status', 'count'], c)) for c in status_counts]


def events_by_types(event_ids):
    """
    Count the number of events associated with event types.
    """
    status_counts = db.session\
        .query(Event.type, func.count(Event.type))\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(Event.type)))\
        .group_by(Event.type).all()
    return [dict(zip(['type', 'count'], c)) for c in status_counts]


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
    return [dict(zip(['type', 'count'], r)) for r in type_counts]


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
    return [dict(zip(['domain', 'count'], r)) for r in domain_counts]


def things_by_recipes(thing_ids):
    """
    Count the number of things associated with recipes.
    """
    recipe_counts = db.session\
        .query(Recipe.id, func.count(Recipe.id))\
        .join(Thing)\
        .filter(Thing.id.in_(thing_ids))\
        .order_by(desc(func.count(Recipe.id)))\
        .group_by(Recipe.id).all()
    return [dict(zip(['id', 'count'], r)) for r in recipe_counts]


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
    return [dict(zip(['id', 'count'], c)) for c in tag_counts]


def things_by_sous_chefs(thing_ids):
    """
    Count the number of things associated with sous chefs.
    """
    task_counts = db.session\
        .query(SousChef.id, func.count(SousChef.id))\
        .outerjoin(Recipe)\
        .outerjoin(Thing)\
        .filter(Thing.id.in_(thing_ids))\
        .order_by(desc(func.count(SousChef.id)))\
        .group_by(SousChef.id).all()
    return [dict(zip(['id', 'count'], c)) for c in task_counts]
