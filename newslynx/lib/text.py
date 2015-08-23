"""
All things related to text formatting.
"""

from unidecode import unidecode
from slugify import slugify as _slugify

from newslynx.lib.regex import re_whitespace

# force weird symbols to ascii approximations
UNICODE_SYMBOLS = {
    u"\u2013": u"-",
    u"\u2014": u"-",
    u"\u2015": u"-",
    u"\u2017": u"+",
    u"\u2018": u"'",
    u"\u2019": u"'",
    u"\u201A": u",",
    u"\u201B": u"'",
    u"\u201C": u'"',
    u"\u201D": u'"',
    u"\u201E": u",,",
    u"\u2020": u" ",
    u"\u2021": u" ",
    u"\u2022": u"*",
    u"\u2026": u". . .",
    u"\u2030": u"%",
    u"\u2032": u"'",
    u"\u2033": u"",
    u"\u2039": u">",
    u"\u203A": u"<",
    u"\u203C": u"!!",
    u"\u203E": u" ",
    u"\u2044": u"/",
    u"\u204A": u"7"
}


def unicode_symbols(s):
    """
    Reconcile unicode symbols to ascii characters.
    """
    for k, v in UNICODE_SYMBOLS.items():
        s = s.replace(k, v)
    return s


def prepare(s):
    """
    Prepare text.
    """
    s = unicode_symbols(s)
    s = re_whitespace.sub(' ', s).strip()
    try:
        s = unidecode(s)
    except Warning:
        pass
    return s


def slug(s, **kwargs):
    """
    Slugify a string.
    """
    s = s.strip()
    if not isinstance(s, unicode):
        s = unicode(s, errors='ignore')
    return _slugify(s, **kwargs)
