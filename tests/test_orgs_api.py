import unittest
from faker import Faker

from newslynx.client import API
from newslynx import settings

fake = Faker()


class TestOrgAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_list(self):
        orgs = self.api.orgs.list()
        assert(isinstance(orgs, list))
        assert(self.org in [o['id'] for o in orgs])

    def test_get(self):
        org1 = self.api.orgs.get()
        org2 = self.api.orgs.get(org=self.org)
        assert org1['id'] is not None and org1['id'] == org2['id']

    def test_create(self):
        n = fake.name()
        org1 = self.api.orgs.create(name=n, timezone='America/New_York')
        assert org1['name'] == n
        assert(settings.SUPER_USER_EMAIL in [u['email'] for u in org1['users']])
        self.api.orgs.delete(org1['id'])

    def test_update(self):
        n = fake.name()
        org1 = self.api.orgs.update(org=self.org, name=n)
        assert org1['name'] == n

    def test_delete(self):
        n = fake.name()
        org1 = self.api.orgs.create(name=n, timezone='America/New_York')
        resp = self.api.orgs.delete(org=org1['id'])
        assert resp
        orgs = self.api.orgs.list()
        assert(org1['id'] not in [o['id'] for o in orgs])

    def test_list_users(self):
        users = self.api.orgs.list_users()
        assert(settings.SUPER_USER_EMAIL in [u['email'] for u in users])

    def test_get_user(self):
        user = self.api.orgs.get_user(user=settings.SUPER_USER_EMAIL)
        assert(self.org in [o['id'] for o in user['orgs']])

    def test_create_user(self):
        email = fake.name().replace(' ', '').strip() + "@foo.com"
        user = self.api.orgs.create_user(email=email, password='foo', name=fake.name())
        assert(self.org in [o['id'] for o in user['orgs']])

    def test_remove_user(self):
        email = fake.name().replace(' ', '').strip() + "@foo.com"
        user = self.api.orgs.create_user(email=email, password='foo', name=fake.name())
        resp = self.api.orgs.remove_user(user=user['id'])
        assert resp
        org = self.api.orgs.get(org=self.org)
        assert(user['id'] not in [u['id'] for u in org['users']])

    def test_add_user(self):
        email = fake.name().replace(' ', '').strip() + "@foo.com"
        user = self.api.orgs.create_user(email=email, password='foo', name=fake.name())
        resp = self.api.orgs.remove_user(user=user['id'])
        assert resp
        user = self.api.orgs.add_user(user=user['id'])
        org = self.api.orgs.get(org=self.org)
        assert(user['id'] in [u['id'] for u in org['users']])

if __name__ == '__main__':
    unittest.main()
