import datetime

import unittest
import pytz

from newslynx.lib import article


class TestArticleExtraction(unittest.TestCase):

    def test_propublica(self):

        source_url = 'https://www.propublica.org/article/congress-to-consider-scaling-down-group-homes-for-troubled-children'
        d = article.extract(source_url)
        assert(['JOAQUIN SAPIEN'] == d['authors'])
        assert(d['page_type'] == 'article')
        assert(d['title'] == 'Congress to Consider Scaling Down Group Homes for Troubled Children')
        assert(d['description'] == 'At a hearing in Washington, a renewed call for addressing the violence and neglect that plagues group homes for foster youth.')
        assert(d['domain'] == 'propublica.org')
        assert(d['site_name'] == 'ProPublica')
        assert(d['created'] == datetime.datetime(2015, 5, 20, 17, 47, 13, tzinfo=pytz.utc))
        assert(d['favicon'] == 'https://www.propublica.org/favicon.ico')
        assert(d['img_url'] == 'https://www.propublica.org/images/ngen/gypsy_og_image/20150520-group-home-hearing-1200x630.jpg')
        assert('finding that children had repeatedly been sent to facilities that were rife with abuse and that had become known recruiting grounds for pimp' in d['content'])
        assert(d['url'] == source_url)
        assert('http://media.miamiherald.com/static/media/projects/2014/innocents-lost/' in d['links'])

    def test_reveal(self):
        source_url = 'https://www.revealnews.org/article/a-brief-history-of-the-modern-strawberry/'
        d = article.extract(source_url)
        assert(d['page_type'] == 'article')
        assert(d['title'] == 'A Brief History of the Modern Strawberry')
        assert(d['description'] == 'This short stop-motion animation explains how clever advertising tactics and certain pesticides helped make the strawberry cheaply and widely available in the U.S.')
        assert(d['domain'] == 'revealnews.org')
        assert(d['site_name'] == 'Reveal')
        assert(d['created'] == datetime.datetime(2014, 11, 11, 0, 57, tzinfo=pytz.utc))
        assert(d['favicon'] == 'https://www.revealnews.org/wp-content/themes/reveal2015/static/images/cir/favicon.ico')
        assert(d['img_url'] == 'https://www.revealnews.org/wp-content/uploads/2015/02/Strawberry-CA0.png')
        assert('it seems that strawberries are served with just about everything' in d['content'])
        assert(d['url'] == source_url)
        assert('http://www.youtube.com/watch?v=fPxUIz5GHAE' in d['links'])

if __name__ == '__main__':
    unittest.main()
