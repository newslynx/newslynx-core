import unittest

from newslynx.client import API
from newslynx import settings

from faker import Faker

fake = Faker()


class TestUserAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_login(self):
        me = self.api.login(
            email=settings.ADMIN_EMAIL, password=settings.ADMIN_PASSWORD)
        assert True

    def test_get(self):
        me = self.api.me.get()
        assert self.org in [o['id'] for o in me['orgs']]
        assert True

    def test_update_name(self):
        me1 = self.api.me.get()
        me2 = self.api.me.update(name=fake.name())
        assert me1['name'] != me2['name']
        me3 = self.api.me.update(name=me1['name'])
        assert me1['name'] == me3['name']

    def test_update_email(self):
        me1 = self.api.me.get()
        me2 = self.api.me.update(email=fake.name())
        assert me1['email'] != me2['email']
        me3 = self.api.me.update(email=settings.ADMIN_EMAIL)
        assert me1['email'] == me3['email']

    def test_update_password(self):
        self.api.me.update(old_password=settings.ADMIN_PASSWORD, new_password='foo')
        self.api.me.update(old_password='foo', new_password=settings.ADMIN_PASSWORD)
        self.api.login(email=settings.ADMIN_EMAIL, password=settings.ADMIN_PASSWORD)

if __name__ == '__main__':
    unittest.main()
