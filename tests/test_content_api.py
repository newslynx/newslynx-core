import unittest
import re
from faker import Faker

from newslynx.client import API
from newslynx.models import ExtractCache
from newslynx.constants import CONTENT_ITEM_FACETS

# flush the cache to ensure fresh results.
ExtractCache.flush()


fake = Faker()


class TestContentAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_create_content_item_manual_extract(self):
        c = {
            'url': 'https://projects.propublica.org/killing-the-colorado/story/wasting-water-out-west-use-it-or-lose-it',
            'type': 'article',
            'tag_ids': [13, 14]
        }
        c = self.api.content.create(extract=True, **c)
        assert(len(c['tag_ids']) == 2)
        assert(len(c['authors']) == 1)
        assert(c['provenance'] == 'manual')

    def test_create_content_item_recipe_extract(self):
        c = {
            'url': 'http://www.nytimes.com/2015/06/10/world/middleeast/us-adding-military-advisers-to-reclaim-iraqi-city-officials-say.html?hp&action=click&pgtype=Homepage&module=first-column-region&region=top-news&WT.nav=top-news',
            'type': 'article',
            'recipe_id': 1,
        }
        c = self.api.content.create(extract=True, **c)
        assert(c['provenance'] == 'recipe')

    def test_create_content_item_non_extract_author_ids(self):
        c = {
            'url': 'http://labs.enigma.io/climate-change-map',
            'type': 'interactive',
            'title': 'This was a story about global warming.',
            'authors': [1, 2]
        }
        c = self.api.content.create(extract=False, **c)
        assert(len(c['authors']) == 2)

    def test_content_facets(self):
        c = self.api.content.search(facets='all')
        assert len(c.facets.keys()) == len(CONTENT_ITEM_FACETS)

    def test_content_search(self):
        c = self.api.content.get(1)
        cis = self.api.content.search(
            q=c.title, search='title', sort='relevance')
        assert(cis.content_items[0].title == c.title)

    def test_content_bad_type(self):
        try:
            self.api.content.search(type='foo')
        except Exception as e:
            assert(e.status_code == 400)
        else:
            assert(False)

    def test_content_bad_provenance(self):
        try:
            self.api.content.search(provenance='foo')
        except Exception as e:
            assert(e.status_code == 400)
        else:
            assert(False)

    def test_content_domain_filter(self):
        cis = self.api.content.search(domain='foodflikjalsdf')
        assert(len(cis.content_items) == 0)

    def test_content_url_regex(self):
        cis = self.api.content.search(url_regex='.*example.*')
        if len(cis.content_items):
            assert(re.search('.*example.*', cis.content_items[0].url))

    def test_update_content(self):
        n = fake.name()
        c = self.api.content.get(1)
        c1 = self.api.content.update(1, title=n)
        assert(c1.title == n)
        assert(c1.title != c.title)

    def test_delete_content(self):
        cis = self.api.content.search(sort='title')
        c = cis.content_items[0]
        ts = self.api.content.get_timeseries(c.id)
        assert(len(ts))
        r = self.api.content.delete(c.id)
        assert(r)
        try:
            self.api.content.get_timeseries(c.id)
        except Exception as e:
            assert(e.status_code == 404)

    def test_add_remove_subject_tag(self):
        tags = self.api.tags.list(type='subject')
        t = tags.tags[0]
        cis = self.api.content.search(sort='id', tag_ids='!{}'.format(t.id))
        c1 = cis.content_items[0]
        c2 = self.api.content.add_tag(c1.id, t.id)
        assert(len(c2.tag_ids) > len(c1.tag_ids))
        c3 = self.api.content.remove_tag(c1.id, t.id)
        assert(len(c3.tag_ids) == len(c1.tag_ids))


if __name__ == '__main__':
    unittest.main()
