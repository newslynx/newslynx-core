from newslynx.sc import SousChef
from pprint import pprint


class Article(SousChef):

    def run(self):
        print "ORG"
        pprint(self.org)
        print "SETTINGS"
        pprint(self.settings)
        print "AUTHS"
        pprint(self.auths)
        print "USERS"
        pprint(self.users)
        print "OPTIONS"
        pprint(self.options)
