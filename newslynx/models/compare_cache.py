"""
Compute and cache content metric comparisons.
"""
from gevent.pool import Pool

from sqlalchemy import func

from newslynx.core import db
from newslynx.tasks.compare_metric import ContentComparison
from newslynx.core import settings
from newslynx.models import (
    Org, Tag, Event, ContentItem)
from newslynx.models.relations import (
    content_items_tags,
    content_items_events)

from newslynx.models.cache import Cache


class ComparisonCache(Cache):
    key_prefix = settings.COMPARISON_CACHE_PREFIX
    ttl = settings.COMPARISON_CACHE_TTL

    def get_facets(self, org, **kw):
        raise NotImplemented

    def get_content_item_ids(self, org, facet, **kw):
        raise NotImplemented

    def format_comparisons(self, comparisons):
        return {self.name: comparisons}

    # add extra key for hashing.
    def format_key(self, *args, **kw):
        kw.update({'name__': self.name})
        return self._format_key(*args, **kw)

    # TODO: Pooled Exectution
    def work(self, org_id, **kw):
        org = db.session.query(Org).get(org_id)
        metrics = org.content_metric_comparisons
        comparisons = {}
        for facet in self.get_facets(org, **kw):
            ids = self.get_content_item_ids(org, facet, **kw)
            if len(ids):
                cc = ContentComparison(org, ids, metrics)
                comparisons[facet] = list(cc.execute())
        db.session.remove()
        return self.format_comparisons(comparisons)


class ComparisonsCache(Cache):

    """
    Get/cache all comparisons.
    """
    key_prefix = settings.COMPARISON_CACHE_PREFIX
    ttl = settings.COMPARISON_CACHE_TTL
    pool_size = 4

    @property
    def comparison_lookup(self):
        return {
            'all': AllContentComparisonCache(),
            'types': ContentTypeComparisonCache(),
            'subject_tags': SubjectTagsComparisonCache(),
            'impact_tags': ImpactTagsComparisonCache()
        }

    def invalidate(self, *args, **kwargs):
        """
        Invalidate all caches.
        """
        for cache in self.comparison_lookup.values():
            cache.invalidate(*args, **kwargs)
        self.redis.delete(self.format_key(*args, **kwargs))

    def work(self, org_id):

        types = self.comparison_lookup.keys()

        def fx(type):
            cobj = self.comparison_lookup[type]
            if self.debug:
                cobj.debug = True
            cr = cobj.get(org_id)
            return cr.value

        comparisons = {}
        for typ in types:
            comparisons.update(fx(typ))
        return comparisons


class AllContentComparisonCache(ComparisonCache):

    name = "all"

    def get_facets(self, org, **kw):
        return ["all"]

    def get_content_item_ids(self, org, facet, **kw):
        return org.content_item_ids

    def format_comparisons(self, comparisons):
        return comparisons


class SubjectTagsComparisonCache(ComparisonCache):

    name = "subject_tags"

    def get_facets(self, org, **kw):
        """
        Get all subject tag ids.
        """
        tag_ids = db.session.query(Tag)\
            .filter_by(org_id=org.id)\
            .filter_by(type='subject')\
            .with_entities(Tag.id)\
            .all()
        return [t[0] for t in tag_ids]

    def get_content_item_ids(self, org, tag_id, **kw):
        """
        Get all content item ids for a Tag.
        """
        content_items = db.session\
            .query(func.distinct(content_items_tags.c.content_item_id))\
            .filter(content_items_tags.c.tag_id == tag_id)\
            .all()
        return [c[0] for c in content_items]


class ImpactTagsComparisonCache(ComparisonCache):

    name = "impact_tags"

    def get_facets(self, org, **kw):
        """
        Get all subject tag ids.
        """
        tag_ids = db.session.query(Tag)\
            .filter_by(org_id=org.id)\
            .filter_by(type='impact')\
            .with_entities(Tag.id)\
            .all()
        return [t[0] for t in tag_ids]

    def get_content_item_ids(self, org, tag_id, **kw):
        """
        Get all content item ids for a Tag.
        """
        content_items = db.session\
            .query(func.distinct(content_items_events.c.content_item_id))\
            .join(Event)\
            .filter(Event.tags.any(Tag.id == tag_id))\
            .all()
        return [c[0] for c in content_items]


class ContentTypeComparisonCache(ComparisonCache):

    name = "types"

    def get_facets(self, org, **kw):
        types = db.session.query(func.distinct(ContentItem.type))\
            .filter_by(org_id=org.id)\
            .all()

        return [t[0] for t in types]

    def get_content_item_ids(self, org, type, **kw):
        content_items = db.session.query(func.distinct(ContentItem.id))\
            .filter_by(org_id=org.id)\
            .filter_by(type=type)\
            .all()

        return [c[0] for c in content_items]
