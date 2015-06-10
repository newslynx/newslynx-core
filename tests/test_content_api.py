import unittest

from newslynx.client import API
from newslynx.models import ExtractCache

# flush the cache to ensure fresh results.
ExtractCache.flush()


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


if __name__ == '__main__':
    unittest.main()
