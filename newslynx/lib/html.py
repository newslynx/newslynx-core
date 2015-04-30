"""
All things related to html parsing.
"""

from HTMLParser import HTMLParser
from HTMLParser import HTMLParseError
import re
from bs4 import BeautifulSoup
from urlparse import urlparse
from urlparse import urljoin

# html stripping


class MLStripper(HTMLParser):

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def make_soup(htmlstring):
    """
    Helper.
    """
    return BeautifulSoup(htmlstring)


def strip_tags(htmlstring):
    """
    string tags and clean text from html.
    """
    s = MLStripper()
    s.feed(htmlstring)
    raw_text = s.get_data()
    raw_text = re.sub(r'\n|\t|\r', ' ', raw_text)
    return re.sub('\s+', ' ', raw_text).strip()


def get_meta(page_html, url):
    """
    get title, description, favicon, twitter card, 
    facebook open graph data

    This is taken from https://github.com/nytlabs/pageinfo

    Since every transformation step produce incomplete 
    versions of the same normalized schema, we 
    can optimistically try to get lots of things.
    """
    data = {'meta': {}}
    data['url'] = url
    data['title'] = None
    data["summary"] = None
    data['meta']["favicon"] = None
    data['meta']["facebook"] = {}
    data['meta']["twitter"] = {}

    try:
        soup = make_soup(page_html)

        # get title
        if soup.title.string:
            data['title'] = soup.title.string

        # get favicon
        parsed_uri = urlparse(url)
        if soup.find("link", rel="shortcut icon"):
            icon_rel = soup.find("link", rel="shortcut icon")["href"]
            icon_abs = urljoin(url, icon_rel)
            data['meta']["favicon"] = icon_abs
        else:
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            data['meta']["favicon"] = domain + 'favicon.ico'

        # get description
        if soup.find('meta', attrs={'name': 'description'}):
            data["summary"] = soup.find(
                'meta', attrs={'name': 'description'})["content"]

        # get facebook open graph data
        if soup.find_all('meta', {"property": re.compile("^og")}):
            for tag in soup.find_all('meta', {"property": re.compile("^og")}):
                tag_type = tag['property']
                data['meta']["facebook"][tag_type] = tag['content']
                if tag_type == "og:description" and data["summary"] is None:
                    data["summary"] = tag["content"]

        # get twitter card data
        if soup.find_all('meta', attrs={'name': re.compile("^twitter")}):
            for tag in soup.find_all('meta', attrs={'name': re.compile("^twitter")}):
                tag_type = tag['name']
                if 'content' in tag.attrs:
                    data['meta']["twitter"][tag_type] = tag['content']
                    if tag_type == "twitter:description" and data["summary"] is None:
                        data["summary"] = tag["content"]

        # make sure canonical exists, use og as backup
        if not data['url'] or len(data['url']) == 0:
            if data['facebook'].has_key('og:url'):
                data['url'] = data['facebook']['og:url']

        return data

    except HTMLParseError:
        return {"canonical": url, "error": "Error parsing page data"}
