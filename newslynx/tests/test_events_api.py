import unittest
from faker import Faker

from newslynx.client import API
from newslynx import settings

fake = Faker()


class TestEventsAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_search(self):
        events = self.api.events.search()
        print events

if __name__ == '__main__':
    unittest.main()
