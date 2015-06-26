import unittest

from newslynx.client import API

good_recipe = {
    "name": "My Cool Twitter List Recipe",
    "sous_chef": "facebook-page-to-event",
    "status": "uninitialized",
    "user_id": 1,
    "last_job": {},
    "page_name": "helloworld"
}

## TODO ACTUALLY WRITE THESE TESTS


class TestRecipeAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_create(self):
        recipe = self.api.recipes.get(1)
        print recipe
        assert(recipe['status'] == 'uninitialized')
        recipe = self.api.recipes.update(1, feed_url='yo')
        print recipe
        assert(recipe['status'] == 'stable')
        self.api.recipes.delete(recipe['id'])
        recipe = self.api.recipes.get(recipe['id'])
        assert(recipe['status'] == 'inactive')

if __name__ == '__main__':
    unittest.main()
