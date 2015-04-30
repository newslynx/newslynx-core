"""
All things related to content/metadata extraction Apis / Engines.
"""

import copy
from collections import defaultdict
from operator import itemgetter

import requests
from readability.readability import Document

from newslynx.core import embedly_api
from newslynx.core import bitly_api
# from newslynx.core import s3
from newslynx.lib import urls
from newslynx.lib import images
from newslynx.lib import authors
from newslynx.lib import html
from newslynx.lib import dates
from newslynx.lib.serialize import obj_to_json
# from newslynx.lib import network


def extract(**kw):

    return _Extract().run(**kw)


class _Extract:

    """
    General purpose content extraction and normalization.

    Give it one url, it will return the following 
    schema:

    {
            "hash": "fhhl424",
            "url": "http://newslynx.org", # canonicalized url
            "slug": a slug of the path, eg "world-africa-2014-06-07-violence-in-kenya", we can use this to link urls per organization, they'll also look nice in a url e.g.
            "short_link": "nwsln.cx/fhhl424", # we'll create custom short urls for every content item.
                                                                              # we can then lookup gloabl bitly information.
            "authors": ["id"], "raw/<canvas></canvas>onicalized creator ids."
            "links": [],     # canonicalized ids of the content that 
                                             # the item links to. 
                                             # for every piece of content we see, we'll 
                                             # also extract all the "content-looking" 
                                             # urls and create new content items 
                                             # This way we can build up a rich 
                                             # network of content-links 
            "article_links": [], 
            "created_at": 1234,
            "title": "Newslynx on trial for Sorcery",
            "summary": "Magic is not a crime." ,
            "embed": "<>",
            "img_url": "s3://"
            "meta": {
                    "entities": [],
                    "keywords": []
            }
    }


    """

    def __init__(self):
        pass

    # @network.retry(attempts=2, status_codes=[200])
    def _get(self, u):
        return requests.get(u)

    def _setup_cache(self):
        # set cache dir settings
        c = "things/{@date_path}/{hash}"
        self.jsonc = c + ".json.gz"
        self.htmlc = c + ".html"

    def _run(self, **kw):

        # check for url
        if 'url' not in kw:
            raise ValueError('Extract requires at minimum, a url.')

        # setup cache:
        self._setup_cache()

        # url normalization.
        thing = copy.deepcopy(kw)
        thing['url'] = kw.get('url')

        thing['source_domain'] = kw.get('source_domain',
                                        urls.get_domain(thing['url']))

        thing['url'] = urls.prepare(thing['url'],
                                    source=thing['source_domain'])

        thing['short_url'], thing['hash'] = \
            urls.shorten(thing['url'])

        thing['slug'] = urls.get_slug(thing['url'])

        # check if we've already parsed this.
        if s3j.exists(self.jsonc, **thing):
            return s3j.get(self.jsonc, **thing)

        # check if we've already parsed the html recently.
        if s3.exists(self.htmlc, **thing):
            page_source = s3.get(self.htmlc, **thing)

        # get the pages html, page source is s3 url!
        else:
            r = self._get(thing['url'])
            page_source = r.content
            thing['page_source'] = s3.put(r.content, self.htmlc, **thing)

        # add stuff to thing depending on whats already been provided.
        if not thing.get('text'):

            thing.update(via_readability(page_source))
            thing.update(via_newspaper(thing['url']))

        # check for authors in page metadata
        if 'authors' not in thing:
            thing['authors'] = \
                authors.from_html(page_source)

        # check for metadata fields
        meta = html.get_meta(page_source, thing['url'])

        # get the title from metadata
        if not thing.get('title'):
            thing['title'] = meta['title']

        # make sure we get some sort of summary.
        if not thing.get('summary'):
            thing['summary'] = meta.get('summary')

        # throw in whatever else we have.
        thing['meta'].update(meta['meta'])

        # make sure we record links
        if not thing.get('links'):
            thing['links'] = urls.from_html(
                thing.get('article_html', page_source)
            )

        # cache this.
        s3j.put(thing, self.jsonc, **thing)
        return thing

    def run(self, **kw):
        return self._run(**kw)


def via_embedly(u):
    """
    Is the best so far :)
    """

    # extract content from elasticsearch
    e = embedly_api.extract(u)

    # check for errors.
    if e['type'] == 'error':
        return {}

    # normalize.
    else:

        # lists
        keywords = [k.get('name') for k in e.get('keywords', [])]
        entities = [n.get('name') for n in e.get('entities', [])]
        authors = [k.get('name') for k in e.get('authors', [])]
        related = [r.get('url') for r in e.get('related', [])]

        # top img, by size.
        img_url = None
        if 'images' in e and len(e['images']):
            sorted_imgs = sorted(
                e['images'], key=itemgetter('size'), reverse=True)
            if len(sorted_imgs):
                img_url = sorted_imgs[0]['url']

        # embed
        embed = e.get('content', e.get('media'))

        # output
        return {
            'url': e.get('url'),
            'img_url': img_url,
            'summary': e.get('description'),
            'title': e.get('title'),
            'embed': embed,
            'text': html.strip_tags(embed),
            'links': urls.from_html(embed),
            'authors': authors,
            'meta': {
                'keywords': keywords,
                'entities': entities,
                'favicon': e.get('favicon_url'),
                'related_links': related
            }
        }


def via_newspaper(u):
    """
    Newspaper is good at metadata
    """
    np = newspaper.Article(url=u, keep_article_html=True)
    np.download()
    np.parse()
    np.nlp()

    # normalize to `Thing` schema.
    return {
        'img_url': np.top_img,
        'embed': np.article_html,
        'text': html.strip_tags(np.article_html),
        'links': urls.from_html(np.article_html),
        'summary': np.summary if not np.meta_description else np.meta_description,
        'meta': {
            'keywords': np.keywords,
            'favicon': np.meta_favicon,
            'language': np.meta_lang
        }
    }


def via_readability(page_source):
    """	
    Readbility is good at article + title.
    """

    obj = Document(page_source)
    embed = obj.summary()
    if embed is not None:
        return {
            'embed': embed,
            'text': html.strip_tags(embed),
            'title': obj.short_title(),
            'links': urls.from_html(embed)
        }
    else:
        return {}

if __name__ == '__main__':
    d = via_embedly(
        'http://www.propublica.org/article/mumbai-attack-data-an-uncompleted-puzzle')
    print obj_to_json(d)
