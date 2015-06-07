import unittest
from faker import Faker

from newslynx.client import API

fake = Faker()


class TestTagsAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_create_subject_tag(self):
        n = fake.name()
        t = self.api.tags.create(name=n, type='subject', color='#fc0')
        assert t.name == n

    def test_list(self):
        n = fake.name()
        t = self.api.tags.create(name=n, type='subject', color='#fc0')
        assert t.name == n
        tags = self.api.tags.list()
        assert(n in [t.name for t in tags['tags']])
        assert(set(['types', 'levels', 'categories']) == set(tags['facets'].keys()))
        assert(tags.facets.types.subject > 1)

    def test_create_impact_tag(self):
        n = fake.name()
        t = self.api.tags.create(name=n, type='impact', color='#fc0', category='promotion', level='media')
        assert(t.name == n)

    def test_create_subject_tag_error(self):
        n = fake.name()
        try:
            t = self.api.tags.create(name=n, type='subject', color='#fc0', category='promotion', level='media')
        except Exception as e:
            assert e.status_code == 400

    def test_update_tag(self):
        n = fake.name()
        t1 = self.api.tags.create(name=n, type='impact', color='#fc0', category='promotion', level='media')
        t2 = self.api.tags.update(t1.id, color='#cf0', category='change', level='institution')
        assert t1.color != t2.color
        assert t1.category != t2.category
        assert t1.level != t2.level

    def test_delete_tag(self):
        n = fake.name()
        t1 = self.api.tags.create(name=n, type='impact', color='#fc0', category='promotion', level='media')
        resp = self.api.tags.delete(t1.id)
        assert resp
        tags = self.api.tags.list().tags
        assert (t1.id not in [t.id for t in tags])

if __name__ == '__main__':
    unittest.main()
