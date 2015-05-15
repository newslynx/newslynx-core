from sqlalchemy import func, desc

from newslynx.models import Event, Recipe, Tag, SousChef, Thing
from newslynx.models.relations import events_tags
from newslynx.core import celery, db


@celery.task
def events_by_recipes(event_ids):
    """
    Count the number of events associated with recipes.
    """
    recipe_counts = db.session\
        .query(Event.recipe_id, Recipe.slug, func.count(Recipe.id))\
        .join(Recipe)\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(Recipe.id)))\
        .group_by(Event.recipe_id, Recipe.slug)\
        .all()

    return [dict(zip(['id', 'slug', 'count'], r)) for r in recipe_counts]


@celery.task
def events_by_tags(event_ids):
    """
    Count the number of events associated with tags.
    """
    tag_counts = db.session\
        .query(Tag.id, Tag.name, Tag.type, Tag.level, Tag.category, Tag.color, func.count(Tag.id))\
        .outerjoin(events_tags)\
        .filter(events_tags.c.event_id.in_(event_ids))\
        .order_by(desc(func.count(Tag.id)))\
        .group_by(Tag.id, Tag.name, Tag.type, Tag.level, Tag.category, Tag.color)\
        .all()
    return [dict(zip(['id', 'name', 'type', 'level', 'category', 'color', 'count'], c))
            for c in tag_counts]


@celery.task
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


@celery.task
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


@celery.task
def events_by_sous_chefs(event_ids):
    """
    Count the number of events associated with sous chefs.
    """
    sous_chef_counts = db.session\
        .query(SousChef.id, SousChef.slug, func.count(SousChef.slug))\
        .join(Recipe)\
        .join(Event)\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(SousChef.slug)))\
        .group_by(SousChef.id, SousChef.slug)
    return [dict(zip(['id', 'slug', 'count'], c)) for c in sous_chef_counts.all()]


@celery.task
def events_by_things(event_ids):
    """
    Count the number of events associated with things.
    """
    thing_counts = db.session\
        .query(Thing.id, Thing.url, Thing.title, func.count(Thing.id))\
        .filter(Thing.events.any(Event.id.in_(event_ids)))\
        .order_by(desc(func.count(Thing.id)))\
        .group_by(Thing.id, Thing.url, Thing.title).all()
    return [dict(zip(['id', 'url', 'title', 'count'], c)) for c in thing_counts]


@celery.task
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


@celery.task
def events_by_types(event_ids):
    status_counts = db.session\
        .query(Event.type, func.count(Event.type))\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(Event.type)))\
        .group_by(Event.type).all()
    return [dict(zip(['type', 'count'], c)) for c in status_counts]
