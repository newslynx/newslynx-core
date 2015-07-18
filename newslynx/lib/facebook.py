

class Facebook(object):
    pass
  


# class FacebookPostEvent(object):

#     def __init__(self, )

# def parse_post(args):
#   post, page_id = args
#   data = {
#     'source_id' : post.get('id', None),
#     'links' : get_urls(post),
#     'img_url' : get_img(post),
#     'datetime' : get_datetime(post),
#     'message' : post.get('message', None),
#     'description' : post.get('description', None),
#     'status_type' : post.get('status_type', None),
#     'type' : post.get('type', None)
#   }
#   return data

# def parse_page_stats(args):
#   page, page_id = args
#   data = {
#     'page_id' : page_id,
#     'page_talking_about_count' : int(page['talking_about_count']),
#     'page_likes' : int(page['likes']),
#     'datetime' : utc_now()
#   }
#   return data

# def parse_insights(args):
#   """
#   Get insights data if indicated so by the config file
#   """
#   insights, page_id, post_id, pub_datetime = args
#   # add metadata
#   insights = {
#     'page_id' : page_id,
#     'post_id' : post_id,
#     'datetime' : utc_now(),
#     'pub_datetime' : pub_datetime
#   }

#   # flatten dict
#   for d in data:
#     val = d['values'][0]['value']
#     if isinstance(val, dict):
#       for k, v in val.iteritems():
#         insights[k] = v

#     else:
#       insights[d['name']] = val

#   return insights

# def get_url_candidates(post):
  
#   urls = set()
  
#   if post.has_key('link'):
#     urls.add(post['link'])

#   if post.has_key('source'):
#     urls.add(post['source'])

#   if post.has_key('message'):
#     msg_urls = parse_message_urls(post['message'])
#     for u in msg_urls: urls.add(u)

#   return list(urls)

# def parse_message_urls(message):
#   urls = urls_from_string(message)
#   return urls

# # TODO: improve this
# def get_img(post):
#   return post.get('picture', None)

# def get_urls(post):
#   candidates = get_url_candidates(post)
#   urls = set()
#   for u in candidates:
#     if 'facebook' not in u:
#       if is_short_url(u):
#         u = unshorten_url(u)
#       urls.add(prepare_url(u))
#   return list(urls)

# def get_datetime(post):
#   if post.get('updated_time'):
#     return strip_date(post['updated_time'])
#   else:
#     return utc_now()