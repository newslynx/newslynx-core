"""
All things related to author parsing.
This module was adapted from newspaper: http://github.com/codelucas/newspaper
"""
from newslynx.lib.regex import *
from newslynx.lib import html

# settings
MIN_NAME_TOKENS = 2  # how short can a name be?
MAX_NAME_TOKENS = 5  # how long can a name be?
DELIM = ['and', '|', '&']
ATTRS = ['name', 'rel', 'itemprop', 'class', 'id']
VALS = ['author', 'byline', 'byl']


def from_html(h):
    """
    Extract author attributes from meta tags.
    Only works for english articles.
    """

    # Search popular author tags for authors

    matches = []
    _authors = []
    soup = html.make_soup(h)

    for attr in ATTRS:
        for val in VALS:
            found = soup.find_all('meta', {attr: val})
            matches.extend(found)

    for match in matches:
        content = u''

        m = match.attrs.get('content', None)
        if m:
            content = m

        else:  # match.tag == <any other tag>
            content = match.text or u''  # text_content()

        if len(content) > 0:
            _authors.extend(from_string(content))

    return _format_authors(_authors)


def from_string(search_str):
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

    _authors, authors = [], []
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
                _authors.append(' '.join(curname))

                # reset
                initial_count = 0
                curname = []

        # otherwise, append token
        elif not re_digits.search(token):
            curname.append(token)

    # One last check at end
    valid_name = (len(curname) >= MIN_NAME_TOKENS)
    if valid_name:
        _authors.append(' '.join(curname))

    return _format_authors(_authors)


# format parsed authors
def _format_authors(_authors):
    """
    Final formatting steps to parsed authors.
    """
    authors = []
    uniq = list(set([a.lower().replace('.', '') for a in _authors if a != '']))

    for name in uniq:
        tokens = [
            w.upper() if re_initial.search(w) else w.title()
            for w in name.split(' ')
        ]
        authors.append(' '.join(tokens))

    return authors


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
