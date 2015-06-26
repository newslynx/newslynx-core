from newslynx.client import API
from pprint import pprint

# connect to the API.
api = API(apikey='mj', org='texas-tribune')

# print the users in this org
print "Current Users"
print "*"*60
pprint(api.orgs.list_users())
print "*"*60

# # create a user
# user = api.orgs.create_user(name='Taylor Swift', email='tay-tay@newslynx.org', password='sh4k31t0ff')
# print "New User"
# print "*"*60
# pprint(user)
# print "*"*60

# login as this user
user = api.login(email='tay-tay@newslynx.org', password='sh4k31t0ff')
print "Tay Tay's API Key"
print "*"*60
pprint(user['apikey'])
print "*"*60