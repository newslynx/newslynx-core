from newslynx.lib import dates 

class FacebookPostEvent(object):

    def __init__(self, **post):
        self.post = post 
        self.page_id = self.post.pop('page_id', None)

    @property
    def source_id(self):


    @property 
    def created(self):
        if self.post.get('updated_time'):
            return dates.parse_iso(post['updated_time'])
        return None

    @property 
    def description(self):
        return self.post.get('description', None)

    @property 
    def title(self):
        return "Facebook post on {}".format(self.page_id)

    @property
    def img_url(self):
        return self.post.get('picture', None)



  if post.get('updated_time'):
    return strip_date(post['updated_time'])
  else:
    return utc_now()



def parse_post(args):
  post, page_id = args
  data = {
    'source_id' : post.get('id', None),
    'links' : get_urls(post),
    'img_url' : get_img(post),
    'datetime' : get_datetime(post),
    'message' : post.get('message', None),
    'description' : post.get('description', None),
    'status_type' : post.get('status_type', None),
    'type' : post.get('type', None)
  }
  return data

def parse_page_stats(args):
  page, page_id = args
  data = {
    'page_id' : page_id,
    'page_talking_about_count' : int(page['talking_about_count']),
    'page_likes' : int(page['likes']),
    'datetime' : utc_now()
  }
  return data

def parse_insights(args):
  """
  Get insights data if indicated so by the config file
  """
  insights, page_id, post_id, pub_datetime = args
  # add metadata
  insights = {
    'page_id' : page_id,
    'post_id' : post_id,
    'datetime' : utc_now(),
    'pub_datetime' : pub_datetime
  }

  # flatten dict
  for d in data:
    val = d['values'][0]['value']
    if isinstance(val, dict):
      for k, v in val.iteritems():
        insights[k] = v

    else:
      insights[d['name']] = val

  return insights

def links(self):
    """
    Extract all links
    """
    urls = []

    if post.get('link'):
        urls.append(self.post['link'])

    if post.get('source'):
        urls.append(self.post['source'])

    if post.get('message'):
        msg_urls = url.from_string(self.post['message'])
        for u in msg_urls: urls.append(u)
    return uniq(urls)

def parse_message_urls(message):
  urls = urls_from_string(message)
  return urls

# TODO: improve this
def get_img(post):
  return 

def get_urls(post):
  candidates = get_url_candidates(post)
  urls = set()
  for u in candidates:
    if 'facebook' not in u:
      if is_short_url(u):
        u = unshorten_url(u)
      urls.add(prepare_url(u))
  return list(urls)

def get_datetime(post):
