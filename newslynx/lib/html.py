"""
All things related to html parsing.
"""

from HTMLParser import HTMLParser
from urlparse import urljoin

import lxml
import lxml.html.clean as clean
from bs4 import BeautifulSoup

from newslynx.lib import text


class MLStripper(HTMLParser):

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(htmlstring):
    """
    String tags and clean text from html.
    """
    s = MLStripper()
    s.feed(htmlstring)
    raw_text = s.get_data()
    return text.prepare(raw_text)


def is_html(htmlstring):
    """
    Detect whether a string is html or not.
    """
    if not htmlstring:
        return False
    return lxml.html.fromstring(htmlstring).find('.//*') is not None


def prepare(htmlstring, source_url=None, safe_attrs=['src', 'href']):
    """
    Cleanse an htmlstring of it's attributes,
    absolutify images and links, ascii-dammify it,
    and clean whitespace.
    """
    if not htmlstring:
        return None
    cleaner = clean.Cleaner(safe_attrs_only=True, safe_attrs=set(safe_attrs))
    cleansed = cleaner.clean_html(htmlstring)
    soup = make_abs(cleansed, source_url)
    cleansed = get_inner(soup)
    return text.prepare(cleansed)


def make_abs(htmlstring, source_url):
    """
    Make "src" and "href" attributes absolute.
    """
    soup = BeautifulSoup(htmlstring)

    # links
    for a in soup.find_all('a'):
        href = a.attrs.get('href')
        if not href:
            continue
        if href.startswith('/') or not href.startswith('http'):
            if source_url:
                a['href'] = urljoin(source_url, href)
        elif href.startswith('#'):
            a.attrs.pop('href')

    # images
    for img in soup.find_all('img'):
        src = img.attrs.get('src')
        if not src:
            continue
        # embeds.
        if src.startswith('//:'):
            img['src'] = "http{}".format(src)
        if src.startswith('/') or not src.startswith('http'):
            if source_url:
                img['src'] = urljoin(source_url, src)
    return soup


def get_inner(n):
    """
    Get the innerhtml from a BeautifulSoup element
    """
    # check if its an entire html or has been parsed by beautiful soup
    _n = n.find('body')
    if _n:
        n = _n
    nodes = [str(x).decode('utf-8', errors='ignore') for x in n.contents]
    return u"".join(nodes)
