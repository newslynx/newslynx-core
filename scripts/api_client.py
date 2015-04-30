from pprint import pprint

from newslynx.client import API
from newslynx import settings
from newslynx.exc import ClientError

# login to the api w/ username and password
api = API(apikey='8bb4e779507b6bf65388c4758414b3d6', org=1)

# login to the api with an apikey
# print ">>> api.login"
# api = API(apikey=api.apikey)
# print "apikey:", api.apikey
# print

# get your user account
# print ">>> api.me"
# me = api.me()
# pprint(me)
# print

# update your user account
# print ">>> api.me_update"
# me = api.me_update(
#     old_password=settings.ADMIN_PASSWORD,
#     new_password='New Password',
#     name='New Name')

# pprint(me)
# print

# change the user back
# me = api.me_update(
#     new_password=settings.ADMIN_PASSWORD,
#     old_password='New Password',
#     name=settings.ADMIN_USER)

# print ">>> api.me_update"
# pprint(me)
# print

# list orgs you have access to
# print ">>> api.me_orgs"
# resp = api.me_orgs()
# pprint(resp)
# print

# create an organization
# if not len(me.organizations):
#     print ">>> api.org_create"
#     org_id = api.org_create(name='ProPalpatine').id
#     pprint(org_id)
#     print
# else:
#     org_id = me.organizations[0].id

# update an organization
# print ">>> api.org_update"
# org = api.org_update(org_id, name='ProPalpatine 2')
# org_id = org.id
# pprint(org)
# print

# change the organization back
# print ">>> api.org_update"
# org = api.org_update(org_id, name='ProPalpatine')
# org_id = org.id
# pprint(org)
# print

# get the current org
# print ">>> api.org"
# org = api.org(org_id)
# pprint(org)
# print

# if not 'foo@bar.com' in [u.email for u in org.users]:
# create a user for this org
#     try:
#         resp = api.org_create_user(
#             org_id,  name='foo', password='bar', email='foo@bar.com')
#         print ">>> api.org_create_user"
#         pprint(resp)
#         print

#         print ">>> api.org_user"
#         org_user = api.org_user(org_id,  'foo@bar.com')
#         pprint(org_user)
#         print

#     except ClientError:
#         print ">>> api.org_add_user"
#         resp = api.org_add_user(org_id, 'foo@bar.com')
#         pprint(resp)
#         print

#         print ">>> api.org_user"
#         org_user = api.org_user(org_id,  'foo@bar.com')
#         pprint(org_user)
#         print
# else:
#     org_user = [u for u in org.users if u.email == 'foo@bar.com'][0]

# remove this user from this org
# print ">>> api.org_remove_user"
# resp = api.org_remove_user(org.id, org_user.id)
# pprint(resp)
# print

# list users under this org
# print ">>> api.org_users"
# resp = api.org_users(org.id)
# pprint(resp)
# print

# add a setting to an organization
# print '>>> api.org_add_setting'
# setting = api.org_add_setting(org.id,
#     name='favicon',
#     value='https://pbs.twimg.com/profile_images/1244937644/02emperor350_400x400.jpg')
# pprint(setting)
# print

# add a json setting to an organization
# print '>>> api.org_add_setting'
# setting = api.org_add_setting(org.id,
#     name='sites',
#     value={'main': 'propalpatine.org', 'tumblr': 'propalpatine.tumblr.com'},
#     json_value=True)
# pprint(setting)
# print

# add a json setting to an organization
# print '>>> api.org_delete_setting'
# resp = api.org_delete_setting(org.id, 'sites')
# pprint(resp)
# print

# get a setting
# print '>>> api.org_setting'
# resp = api.org_setting(org.id, 'favicon')
# pprint(resp)
# print

# get the list of settings
# print '>>> api.org_settings'
# resp = api.org_settings(org.id)
# pprint(resp)
# print

# search events
print '>>> api.events'
resp = api.events(status='pending', per_page=1)
event_id = resp.results[0].id
pprint(resp.results[0].status)
pprint(resp.results[0].tags)
pprint(resp.counts.things)
pprint(resp.updated)
print

# get an event
print '>>> api.event'
resp = api.event(event_id)
pprint(resp.status)
pprint(resp.tags)
pprint(resp.updated)
print

# update an event
print '>>> api.event_update'
resp = api.event_update(
    event_id, thing_ids=[1, 2], tag_ids=[1, 2, 3], description='foo bar')
pprint(resp.status)
pprint(resp.tags)
pprint(resp.things)
pprint(resp.description)
pprint(resp.updated)
print

# update an event
print '>>> api.event_delete'
resp = api.event_delete(event_id)
pprint(resp.status)
pprint(resp.tags)
pprint(resp.things)
pprint(resp.description)
pprint(resp.updated)
print

print '>>> api.events'
resp = api.events(status='approved', per_page=1, sort='updated')
event_id = resp.results[0].id
pprint(resp.results[0].things)
pprint(resp.results[0].tags)
print

print '>>> api.event_add_tag'
resp = api.event_add_tag(event_id, tag_id=3)
pprint(resp.tags)
print

print '>>> api.event_delete_tag'
resp = api.event_delete_tag(event_id, tag_id=3)
pprint(resp.tags)
print

print '>>> api.event_add_tag'
resp = api.event_add_tag(event_id, thing_id=10)
pprint(resp.things)
print

print '>>> api.event_delete_thing'
resp = api.event_delete_thing(event_id, thing_id=10)
pprint(resp.things)
print

# delete the current org
# org = api.delete_org(org.id)
# print "api.delete_org"
# pprint(org)
# print
