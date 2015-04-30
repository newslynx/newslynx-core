"""
All things related to image processing / archiving.
"""

from newslynx.lib import html
from newslynx.lib import urls


def from_html(htmlstring, domain=None, dedupe=True):
    """
    Extract img urls from htmlstring, optionally reconciling
    relative urls
    """
    final_urls = []

    soup = html.make_soup(htmlstring)

    for i in soup.find_all('img'):
        src = i.attrs.get('src', None)
        if src:
            if not urls.is_abs(src):
                if domain:
                    src = prepare(urljoin(domain, src))

            final_urls.append(src)

    if dedupe:
        return list(set(final_urls))
    else:
        return final_urls
