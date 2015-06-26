import unittest
from faker import Faker

from newslynx.client import API

fake = Faker()


class TestAuthorsAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_all(self):
        n1 = fake.name()
        a1 = self.api.authors.create(name=n1)
        assert a1['name'] == n1

        n2 = fake.name()
        a2 = self.api.authors.update(a1['id'], name=n2)
        assert(a1['name'] != a2['name'])

        a3 = self.api.authors.get(a2['id'])
        assert(a3['name'] == a2['name'])

        n3 = fake.name()
        a4 = self.api.authors.create(name=n3)

        ci = self.api.content.get(1)

        a4 = self.api.authors.add_content_item(a4['id'], ci['id'])
        a4 = self.api.authors.get(a4['id'], incl_content=True)
        assert('content_items' in a4)

        a5 = self.api.authors.remove_content_item(a4['id'], ci['id'])
        assert(a5)

        a6 = self.api.authors.get(a2['id'], incl_content=True)
        assert(len(a6['content_items']) == 0)

        a7 = self.api.authors.add_content_item(a4['id'], ci['id'])
        assert(len(a7['content_items']))

        a1 = self.api.authors.merge(a4['id'], a1['id'])
        assert(len(a1['content_items']))


if __name__ == '__main__':
    unittest.main()
