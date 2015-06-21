import unittest
from faker import Faker

from newslynx.client import API

fake = Faker()


class TestMetricsAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_all(self):
        resp = self.api.metrics.list()
        assert(resp.facets.keys() > 1)
        assert(len(resp.metrics) > 1)

        resp = self.api.metrics.list(timeseries=True)
        assert(resp.facets.keys() > 1)
        for m in resp.metrics:
            assert(m.timeseries)

        resp = self.api.metrics.list(cumulative=True)
        assert(resp.facets.keys() > 1)
        for m in resp.metrics:
            assert(m.cumulative)

        resp = self.api.metrics.list(faceted=True)
        assert(resp.facets.keys() > 1)
        for m in resp.metrics:
            assert(m.faceted)

        resp = self.api.metrics.list(aggregations='!median')
        assert(resp.facets.keys() > 1)
        for m in resp.metrics:
            assert(m.aggregation != 'median')

        resp = self.api.metrics.list(aggregations='sum')
        assert(resp.facets.keys() > 1)
        for m in resp.metrics:
            assert(m.aggregation == 'sum')

        m = self.api.metrics.get(1)

        m2 = self.api.metrics.update(m.id, name='foo', display_name='bar')
        assert(m2.name != 'foo')
        assert(m.display_name != m2.display_name)

        r = self.api.metrics.delete(m.id)
        assert(r)

        try:
            self.api.metrics.get(m.id)
            assert False
        except:
            assert True

if __name__ == '__main__':
    unittest.main()
