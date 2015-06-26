from newslynx.client import API
from pprint import pprint

# connect to the API.
api = API(apikey='mj', org='texas-tribune')

# get recipes associated with the rss feed sous chef
recipes = api.recipes.list(sous_chefs='rss-feed-to-article')

r = recipes['recipes'][0]
pprint(r)