import unittest

from newslynx.lib import shares

url = 'http://www.nytimes.com/2015/06/08/world/europe/turkey-election-recep-tayyip-erdogan-kurds-hdp.html'


class TestShareCounts(unittest.TestCase):

    def test_facebook(self):
        counts = shares.count(url, sources='facebook')
        self.assertIn('facebook_shares', counts)

    def test_facebookfql(self):
        counts = shares.count(url, sources='facebookfql')
        self.assertIn('facebook_shares', counts)
        self.assertIn('facebook_comments', counts)
        self.assertIn('facebook_likes', counts)

    def test_google(self):
        counts = shares.count(url, sources='googleplus')
        self.assertIn('googleplus_shares', counts)

    def test_linkedin(self):
        counts = shares.count(url, sources='linkedin')
        self.assertIn('linkedin_shares', counts)

    def test_pinterest(self):
        counts = shares.count(url, sources='pinterest')
        self.assertIn('pinterest_shares', counts)

    def test_reddit(self):
        counts = shares.count(url, sources='reddit')
        self.assertIn('reddit_upvotes', counts)
        self.assertIn('reddit_downvotes', counts)

    def test_twitter(self):
        counts = shares.count(url, sources='twitter')
        self.assertIn('twitter_shares', counts)

    def test_all(self):
        counts = shares.count(url, sources='all')
        self.assertTrue(len(counts.keys()))

if __name__ == '__main__':
    unittest.main()
