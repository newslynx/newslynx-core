import unittest
from faker import Faker

from newslynx.client import API

fake = Faker()


class TestMetricsAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_all(self):
        resp = self.api.metrics.list()
        assert(resp['facets'].keys() > 1)
        assert(len(resp['metrics']) > 1)

        resp = self.api.metrics.list(content_levels='timeseries')
        assert(resp['facets'].keys() > 1)
        for m in resp['metrics']:
            assert('timeseries' in m['content_levels'])

        m = self.api.metrics.list()['metrics'][0]
        n = fake.name()
        m2 = self.api.metrics.update(m['id'], name='foo', display_name=n)
        assert(m2['name'] != 'foo')
        assert(m['display_name'] != m2['display_name'])

        r = self.api.metrics.delete(m['id'])
        assert(r)

        try:
            self.api.metrics.get(m['id'])
            assert False
        except:
            assert True

if __name__ == '__main__':
    unittest.main()
