import unittest

from newslynx.exc import SearchStringError
from newslynx.lib.search import SearchString


class TestSousChefJSONSchema(unittest.TestCase):

    def test_good_search_string(self):
        """A valid search string should provide chained fuzzy matches and regexes"""
        t = SearchString('~world & /.*ello.*/').match('hello worlds')
        assert t

    def test_missing_type(self):
        """A search string cannot have more than two operators."""
        try:
            t = SearchString('~world & /.*ello.*/ OR yo').match('hello worlds')
        except SearchStringError:
            assert True
        else:
            assert False

    def test_good_phrase_search(self):
        """A valid search string should be able to fuzzy match phrases"""
        t = SearchString('~"hello world"').match('hello worlds how are you')
        assert t

    def test_another_good_phrase_search(self):
        """A valid search string should be able to fuzzy match phrases"""
        t = SearchString(
            'fracking AND /.*oil.*/').match('fracking is fun when you get lots of oils')
        assert t

if __name__ == '__main__':
    unittest.main()
