import unittest
import re

from newslynx.client import API
from newslynx.models import ExtractCache
from newslynx.constants import CONTENT_ITEM_FACETS

# flush the cache to ensure fresh results.
ExtractCache.flush()


class TestContentAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    # def test_create_content_item_manual_extract(self):
    #     c = {
    #         'url': 'https://projects.propublica.org/killing-the-colorado/story/wasting-water-out-west-use-it-or-lose-it',
    #         'type': 'article',
    #         'tag_ids': [13, 14]
    #     }
    #     c = self.api.content.create(extract=True, **c)
    #     assert(len(c['tag_ids']) == 2)
    #     assert(len(c['authors']) == 1)
    #     assert(c['provenance'] == 'manual')

    # def test_create_content_item_recipe_extract(self):
    #     c = {
    #         'url': 'http://www.nytimes.com/2015/06/10/world/middleeast/us-adding-military-advisers-to-reclaim-iraqi-city-officials-say.html?hp&action=click&pgtype=Homepage&module=first-column-region&region=top-news&WT.nav=top-news',
    #         'type': 'article',
    #         'recipe_id': 1,
    #     }
    #     c = self.api.content.create(extract=True, **c)
    #     assert(c['provenance'] == 'recipe')

    # def test_create_content_item_non_extract_author_ids(self):
    #     c = {
    #         'url': 'http://labs.enigma.io/climate-change-map',
    #         'type': 'interactive',
    #         'title': 'This was a story about global warming.',
    #         'authors': [1, 2]
    #     }
    #     c = self.api.content.create(extract=False, **c)
    #     assert(len(c['authors']) == 2)

    def test_content_facets(self):
        c = self.api.content.search(facets='all')
        assert len(c.facets.keys()) == len(CONTENT_ITEM_FACETS)

    def test_content_search(self):
        c = self.api.content.get(1)
        cis = self.api.content.search(q=c.title, search='title', sort='relevance')
        assert(cis.content_items[0].title == c.title)

    def test_content_bad_type(self):
        try:
            cis = self.api.content.search(type='foo')
        except Exception as e:
            assert(e.status_code == 400)
        else:
            assert(False)

    def test_content_bad_provenance(self):
        try:
            cis = self.api.content.search(provenance='foo')
        except Exception as e:
            assert(e.status_code == 400)
        else:
            assert(False)

    def test_content_domain_filter(self):
        cis = self.api.content.search(domain='foo')
        assert(len(cis.content_items) == 0)

    def test_content_url_regex(self):
        cis = self.api.content.search(url_regex='.*example.*')
        assert(re.search('.*example.*', cis.content_items[0].url))

    def test_content_url_regex(self):
        cis = self.api.content.search(url_regex='.*example.*')
        assert(re.search('.*example.*', cis.content_items[0].url))






if __name__ == '__main__':
    unittest.main()
