import unittest
from faker import Faker

from newslynx.client import API
from newslynx import settings

fake = Faker()


class TestSettingsAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_create(self):
        n = fake.name()
        s = self.api.settings.create(name=n, value='bar')
        assert s.name == n

    def test_create_json_value(self):
        n = fake.name()
        s = self.api.settings.create(name=n, value=['bar'], json_value=True)
        assert s.json_value
        assert isinstance(s.value, list)

    def test_update(self):
        n = fake.name()
        s1 = self.api.settings.create(name=n, value='bar')
        s2 = self.api.settings.update(s1.name, value='bar2')
        assert s2.value != s1.value

    def test_update_json_vlue(self):
        n = fake.name()
        s1 = self.api.settings.create(name=n, value=['bar'], json_value=True)
        s2 = self.api.settings.update(s1.name, value=['bar2'], json_value=True)
        assert s2.value != s1.value

    def test_get(self):
        n = fake.name()
        s1 = self.api.settings.create(name=n, value='bar')
        assert s1.name == n
        s2 = self.api.settings.get(n)
        assert s1.name == s2.name

    # def test_list(self):
    #     n = fake.name()
    #     s = self.api.settings.create(name=n, value='bar')
    #     assert s.name == n
    #     s = self.api.settings.list()
    #     assert(isinstance(s, list))
    #     assert('bar' in [ss.name for ss in s])

if __name__ == '__main__':
    unittest.main()
