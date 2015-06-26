from newslynx.client import API
from pprint import pprint

# connect to the API.
api = API(apikey='mj')

# print the list of orgs you have access to:
print api.me.orgs()
# >>> []

# create an organization.
org = api.orgs.create(name='Texas Tribune', timezone='US/Mountain')
print "New Org"
print "*"*60
pprint(org)
print "*"*60

# set this org as the one you want to access
api = API(apikey='mj', org=1)

# you should now have access to default tags and recipes.
tags = api.tags.list()
print "New Tags"
print "*"*60
for tag in tags['tags']:
    print "{slug} {type}".format(**tag)
print "*"*60

# you should now have access to default tags and recipes.
recipes = api.recipes.list()
print "New Recipes"
print "*"*60
for recipe in recipes['recipes']:
    print "{slug}".format(**recipe)
print "*"*60
