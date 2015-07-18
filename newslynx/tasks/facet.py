"""
How many of this by that.

These functions all service the event and content search endpoints and are
designed to be executed concurrently in greenlets
(Hence the repetitive db.session.remove())
"""

from collections import defaultdict

from sqlalchemy import func, desc

from newslynx.models import (
    Event, Recipe, Tag, SousChef, ContentItem, Author)
from newslynx.models.relations import (
    events_tags, content_items_tags, content_items_authors,
    content_items_events)
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
    return [dict(zip(['id', 'count'], c)) for c in tag_counts]


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


def events_by_content_items(event_ids):
    """
    Count the number of events associated with content_items.
    """
    thing_counts = db.session\
        .query(ContentItem.id, ContentItem.title, func.count(ContentItem.id))\
        .filter(ContentItem.events.any(Event.id.in_(event_ids)))\
        .order_by(desc(func.count(ContentItem.id)))\
        .group_by(ContentItem.id, ContentItem.url, ContentItem.title).all()

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


def events_by_domains(event_ids):
    """
    Count the number of content_items associated with domains.
    """
    domain_counts = db.session\
        .query(Event.domain, func.count(Event.domain))\
        .filter(Event.id.in_(event_ids))\
        .order_by(desc(func.count(Event.domain)))\
        .group_by(Event.domain).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['domain', 'count'], r)) for r in domain_counts]


def events(by, event_ids):
    """
    Simplified mapping of facet functions
    """
    fx_lookup = {
        'recipes': events_by_recipes,
        'tags': events_by_tags,
        'impact_tags': events_by_tags,
        'categories': events_by_categories,
        'levels': events_by_levels,
        'sous_chefs': events_by_sous_chefs,
        'content_items': events_by_content_items,
        'statuses': events_by_statuses,
        'provenances': events_by_provenances,
        'domains': events_by_domains
    }
    return fx_lookup.get(by)(event_ids)


def event_statuses_by_recipes(recipe_ids):
    """
    Count the number of content_items associated with sous chefs.
    """
    event_counts = db.session\
        .query(Event.recipe_id, Event.status, func.count(Event.status))\
        .filter(Event.recipe_id.in_(recipe_ids))\
        .group_by(Event.recipe_id, Event.status).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    event_counts = [dict(zip(['recipe_id', 'status', 'count'], c)) for c in event_counts]
    d = defaultdict(dict)
    for ec in event_counts:
        if ec['recipe_id'] not in d:
            d[ec['recipe_id']]['total'] = 0
        d[ec['recipe_id']][ec['status']] = ec['count']
        d[ec['recipe_id']]['total'] += ec['count']
    return d


# content_items

def content_items_by_types(content_item_ids):
    """
    Count the number of content_items associated with thing types.
    """
    type_counts = db.session\
        .query(ContentItem.type, func.count(ContentItem.type))\
        .filter(ContentItem.id.in_(content_item_ids))\
        .group_by(ContentItem.type)\
        .order_by(desc(func.count(ContentItem.type)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['type', 'count'], r)) for r in type_counts]


def content_items_by_provenances(content_item_ids):
    """
    Count the number of content_items associated with thing types.
    """
    type_counts = db.session\
        .query(ContentItem.provenance, func.count(ContentItem.provenance))\
        .filter(ContentItem.id.in_(content_item_ids))\
        .group_by(ContentItem.provenance)\
        .order_by(desc(func.count(ContentItem.provenance)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['provenance', 'count'], r)) for r in type_counts]


def content_items_by_domains(content_item_ids):
    """
    Count the number of content_items associated with domains.
    """
    domain_counts = db.session\
        .query(ContentItem.domain, func.count(ContentItem.domain))\
        .filter(ContentItem.id.in_(content_item_ids))\
        .group_by(ContentItem.domain)\
        .order_by(desc(func.count(ContentItem.domain)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['domain', 'count'], r)) for r in domain_counts]


def content_items_by_site_names(content_item_ids):
    """
    Count the number of content_items associated with domains.
    """
    site_name_counts = db.session\
        .query(ContentItem.site_name, func.count(ContentItem.site_name))\
        .filter(ContentItem.id.in_(content_item_ids))\
        .group_by(ContentItem.site_name)\
        .order_by(desc(func.count(ContentItem.site_name)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['site_name', 'count'], r)) for r in site_name_counts]


def content_items_by_authors(content_item_ids):
    """
    Count the number of content_items associated with domains.
    """
    author_counts = db.session\
        .query(content_items_authors.c.author_id,
               Author.name,
               func.count(content_items_authors.c.content_item_id))\
        .join(Author)\
        .filter(content_items_authors.c.content_item_id.in_(content_item_ids))\
        .group_by(content_items_authors.c.author_id, Author.name)\
        .order_by(desc(func.count(content_items_authors.c.content_item_id)))\
        .all()
    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'name', 'count'], r)) for r in author_counts]


def content_items_by_recipes(content_item_ids):
    """
    Count the number of content_items associated with recipes.
    """
    recipe_counts = db.session\
        .query(Recipe.id, func.count(Recipe.slug))\
        .join(ContentItem)\
        .filter(ContentItem.id.in_(content_item_ids))\
        .order_by(desc(func.count(Recipe.id)))\
        .group_by(Recipe.id).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'count'], r)) for r in recipe_counts]


def content_items_by_subject_tags(content_item_ids):
    """
    Count the number of content_items associated with tags.
    """
    tag_counts = db.session\
        .query(content_items_tags.c.tag_id, func.count(content_items_tags.c.tag_id))\
        .filter(content_items_tags.c.content_item_id.in_(content_item_ids))\
        .group_by(content_items_tags.c.tag_id)\
        .order_by(desc(func.count(content_items_tags.c.tag_id)))\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'count'], c)) for c in tag_counts]


def content_items_by_sous_chefs(content_item_ids):
    """
    Count the number of content_items associated with sous chefs.
    """
    task_counts = db.session\
        .query(SousChef.slug, func.count(SousChef.slug))\
        .outerjoin(Recipe)\
        .outerjoin(ContentItem)\
        .filter(ContentItem.id.in_(content_item_ids))\
        .order_by(desc(func.count(SousChef.slug)))\
        .group_by(SousChef.slug).all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['slug', 'count'], c)) for c in task_counts]


def content_items_by_impact_tags(content_item_ids):
    """
    Count the number of content_items associated with sous chefs.
    """
    tag_counts = db.session\
        .query(Tag.id, func.count(Tag.id))\
        .outerjoin(events_tags)\
        .outerjoin(content_items_events, events_tags.c.event_id == content_items_events.c.event_id)\
        .filter(content_items_events.c.content_item_id.in_(content_item_ids))\
        .order_by(desc(func.count(Tag.id)))\
        .group_by(Tag.id)\
        .all()

    # explicitly shutdown session started in greenlet
    db.session.remove()
    return [dict(zip(['id', 'count'], c)) for c in tag_counts]


def content_items(by, content_item_ids):
    """
    Simplified mapping of facet functions
    """
    fx_lookup = {
        'recipes': content_items_by_recipes,
        'authors': content_items_by_authors,
        'subject_tags': content_items_by_subject_tags,
        'impact_tags': content_items_by_impact_tags,
        'sous_chefs': content_items_by_sous_chefs,
        'site_names': content_items_by_site_names,
        'statuses': content_items_by_types,
        'types': content_items_by_types,
        'domains': content_items_by_domains,
        'provenances': content_items_by_provenances
    }
    return fx_lookup.get(by)(content_item_ids)
