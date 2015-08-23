import unittest
import os

from newslynx.init import load_sous_chefs
from newslynx.models import sous_chef_schema

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
FIXTURES_DIR = os.path.join(TEST_DIR, 'fixtures')
SOUS_CHEF_DIR = os.path.join(TEST_DIR, '../{{ name }}')


class Tests(unittest.TestCase):

    def test_schema(self):

        for sc, fp in load_sous_chefs(SOUS_CHEF_DIR, incl_internal=False):
            sous_chef_schema.validate(sc, fp)
        assert True

    ## TODO: Add your tests here.


if __name__ == '__main__':
    unittest.main()
