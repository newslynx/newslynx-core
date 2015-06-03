import datetime

import unittest
import pytz

from newslynx.lib import article


class TestArticleExtraction(unittest.TestCase):

    def test_propublica(self):

        source_url = 'http://www.propublica.org/article/congress-to-consider-scaling-down-group-homes-for-troubled-children'
        d = article.extract(source_url)
        assert(d['page_type'] == 'article')
        assert(d['title'] == 'Congress to Consider Scaling Down Group Homes for Troubled Children')
        assert(d['description'] == 'At a hearing in Washington, a renewed call for addressing the violence and neglect that plagues group homes for foster youth.')
        assert(d['domain'] == 'propublica.org')
        assert(d['site_name'] == 'ProPublica')
        assert(d['created'] == datetime.datetime(2015, 5, 20, 17, 47, 13, tzinfo=pytz.utc))
        assert(d['favicon'] == 'http://www.propublica.org/favicon.ico')
        assert(d['img_url'] == 'http://www.propublica.org/images/ngen/gypsy_og_image/20150520-group-home-hearing-1200x630.jpg')
        assert('finding that children had repeatedly been sent to facilities that were rife with abuse and that had become known recruiting grounds for pimp' in d['content'])
        assert(d['url'] == source_url)

if __name__ == '__main__':
    unittest.main()
