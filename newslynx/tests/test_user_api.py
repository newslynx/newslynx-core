import unittest

from newslynx.client import API
from newslynx import settings

class TestSousChefJSONSchema(unittest.TestCase):

    api = API(org=1)

    def test_login(self):
        resp = self.api.login(email=settings.ADMIN_EMAIL, password=settings.ADMIN_PASSWORD)
        print resp
        assert False

if __name__ == '__main__':
    unittest.main()
