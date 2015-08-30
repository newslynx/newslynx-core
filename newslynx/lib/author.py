"""
Parsing Authors from html meta-tags and strings
This module was adapted from newspaper: http://github.com/codelucas/newspaper
"""
from bs4 import BeautifulSoup

from newslynx.lib.common import make_soup
from newslynx.lib import html
from newslynx.lib.regex import (
    re_by, re_name_token, re_digits,
    re_initial, re_prefix_suffix
)

MIN_NAME_TOKENS = 2  # how short can a name be?
MAX_NAME_TOKENS = 3  # how long can a name be?
DELIM = ['and', '|', '&', '']

PESSIMISTIC_TAGS = ['meta']
OPTIMISTIC_TAGS = [
    'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'p', 'meta', 'div'
]
TAG_ATTRS = [
    'name', 'rel', 'itemprop', 'class', 'id', 'property'
]
TAG_VALS = [
    'author', 'byline', 'byl', 'byline-author', 'post-byline',
    'parsely-author', 'storybyline'
]

# tokens indicative of non-authors (usually photographers)
BAD_TOKENS = [
    'getty', 'images', 'photo', 'january', 'february', 'march',
    'april', 'may', 'june', 'july', 'august', 'september', 'october',
    'november', 'december'
]


def extract(
        soup,
        tags=PESSIMISTIC_TAGS,
        attrs=TAG_ATTRS,
        vals=TAG_VALS):
    """
    Extract author attrs from meta tags.
    Only works for english articles.
    """

    # soupify
    if not isinstance(soup, BeautifulSoup):
        soup = make_soup(soup)

    # Search popular author tags for authors

    matches = []
    _authors = []
    for tag in tags:
        for attr in attrs:
            for val in vals:
                found = soup.find_all(tag, {attr: val})
                matches.extend(found)

    for match in matches:
        content = u''

        m = match.attrs.get('content', None)
        if m:
            content = m

        else:  # match.tag == <any other tag>
            content = match.text or u''  # text_content()
        if len(content) > 0:
            _authors.extend(parse(content))

    return _format(_authors)


def parse(search_str):
    """
    Takes a candidate string and
    extracts out the name(s) in list form
    >>> string = 'By: Brian Abelson, Michael H. Keller and Dr. Stijn Debrouwere IV'
    >>> authors_from_string(string)
    ['Brian Abelson', 'Michael H Keller', 'DR Stijn Debrouwere IV']
    """
    # set initial counter
    initial_count = 0

    # clean string
    search_str = html.strip_tags(search_str)
    search_str = re_by.sub('', search_str)
    search_str = search_str.strip()

    # tokenize
    name_tokens = [s.strip() for s in re_name_token.split(search_str)]

    _authors = []
    curname = []  # List of first, last name tokens

    for token in name_tokens:
        # check if the length of the name
        # and the token suggest an initial
        if _is_initial(curname, token):
            # upper case initial & increment
            token = token.upper()
            initial_count += 1

        # if we're at a delimiter, check if the name is complete
        if token.lower() in DELIM:

            # check valid name based on initial count
            if _end_name(curname, initial_count):
                name = ' '.join(curname)
                if not any([t in name.lower() for t in BAD_TOKENS]):
                    _authors.append(name)

                # reset
                initial_count = 0
                curname = []

        # otherwise, append token
        elif not re_digits.search(token):
            curname.append(token)

    # One last check at end
    valid_name = (len(curname) >= MIN_NAME_TOKENS)
    if valid_name:
        name = ' '.join(curname)
        if not any([t in name.lower() for t in BAD_TOKENS]):
            _authors.append(name)

    return _format(_authors)


# format parsed authors
def _format(authors):
    """
    Final formatting / deduping steps to parsed authors.
    """
    _authors = []
    uniq = list(set([a.lower().replace('.', '')
                     for a in authors if a != '']))
    seen = []
    for name in sorted(uniq, key=len):

        # dedupe multiple html tags with same
        # author info
        if not any([n in name for n in seen]):
            seen.append(name)
            _authors.append(name.upper())

    return _authors


def _match_initial(token):
    """
    Check if a token looks like an initial / prefix / suffix.
    """
    return re_initial.match(token) or re_prefix_suffix.match(token)


def _valid_initial(curname):
    """
    Only include an inital if we haven't passed
    the max name token range.
    """
    return (len(curname) < MAX_NAME_TOKENS + 1)


def _is_initial(curname, token):
    """
    Combination of the above two functions.
    """
    return _valid_initial(curname) and _match_initial(token)


def _end_name(curname, initial_count):
    """
    Check whether we should end the name.
    """
    est_count = MAX_NAME_TOKENS + initial_count
    return (len(curname) <= est_count)
