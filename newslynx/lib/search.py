"""
A search string for a task can have the following formats:

term => match on a term
~term => fuzzy match on a term using jaro_winkler distance
/.*term.*/ => apply a regex
"term1 term2" => match on a phrase
~"term1 term2" => fuzzy match on a phrase

search strings can be chained with the following operators

AND => must match both searchstrings
& => must match both searchstrings
OR => can match either term
| => can match either term

TODO: chained search strings can be grouped with parentheses and subsequently chained, IE:

(~term OR /.*term.*/) AND (/.*term.*/ AND "term1 term2")

you cannot use punctuation in terms.
"""

import re
import string
from copy import copy

import jellyfish
from unidecode import unidecode

from newslynx.exc import SearchStringError
from newslynx.lib.regex import re_whitespace
from newslynx.lib import html
from newslynx.util import uniq

# sets for text cleaning.
punct = frozenset(string.punctuation)
digits = frozenset(string.digits)

# operators
ops = ['|', 'OR', 'AND', '&', '||', '&&']
ops_map = {
    '|': 'OR',
    '&': 'AND',
    '&&': 'AND',
    '||': 'OR',
    'AND': 'AND',
    'OR': 'OR'
}
ops_fx_map = {
    'OR': any,
    'AND': all
}
re_ops = re.compile(
    r'\s+?((?<!\\)[\&]{1,2})\s+?|\s+?(AND)\s+?|\s+?((?<!\\)[\&]{1,2})\s+?|\s+?(OR)\s+?')

MAX_OPS = 1


def linter(s):
    """
    Iterate through terms and determine
    types, parenthetical groups and operator groups
    """

    # split ops
    raw_terms = re_ops.split(s)

    # filter nulls
    raw_terms = [t for t in raw_terms if t]

    # init items
    op = None
    terms = []
    num_ops = 0
    for term in raw_terms:
        td = {}
        td['is_regex'] = False
        td['is_fuzzy'] = False

        if term in ops:
            op = ops_map[term]
            num_ops += 1

            if num_ops > MAX_OPS:
                raise SearchStringError(
                    'You are only allowed to use {} operator(s) in a search string.'
                    .format(MAX_OPS))
        else:
            term = term.lower().decode('utf-8')

            if term.startswith('/') and term.endswith('/'):
                term = re.compile(term[1:-1])
                td['is_regex'] = True

            elif term.startswith('~'):
                td['is_fuzzy'] = True

            elif (term.startswith('"') or term.startswith("'")) and \
                    (term.endswith('"') or term.endswith("'")):
                term = term[1:-1]

            td['term'] = term

            terms.append(td)

    return op, terms


def ngrams(text, n):
    """
    split ngrams
    """
    input_list = text.split(" ")
    return zip(*[input_list[i:] for i in range(n)])


def phrase_grams(term):
    """
    Determine number of ngrams to split by from the term.
    """
    return len(term.split())


# ngram tokenizer
def tokenizer(text, n):
    """
    Tokenize unique ngrams.
    """
    grams = ngrams(text, n)
    return uniq([" ".join(gram).decode('utf-8') for gram in grams])


class SearchString(object):

    """
    A class for simplifiying text searches in recipes.
    """

    # explicitly set the module so we can pickle it:
    # from http://stefaanlippens.net/pickleproblem

    __module__ = 'newslynx.lib.search'

    def __init__(self, raw, fuzzy_threshold=0.88):
        # store raw
        self.raw = raw
        self.fuzzy_threshold = fuzzy_threshold

        try:
            op, terms = linter(raw)
        except Exception as e:
            raise SearchStringError(e.message)
        self.op = op
        if op:
            self.operator = ops_fx_map[op]
        else:
            self.operator = any

        self.terms = terms

    def match(self, text, **kw):
        """
        Apply searchstring logic to text.
        """
        if not text or not len(text):
            return False
        if not isinstance(text, list):
            text = [text]

        for t in text:

            raw = copy(t)
            t = self._process_text(t, **kw)
            tests = []

            for term in self.terms:

                if term['is_regex']:
                    tests.append(self._regex_match(term['term'], t, raw))

                elif term['is_fuzzy']:
                    tests.append(self._fuzzy_match(term['term'], t))

                else:
                    tests.append(self._simple_match(term['term'], t, raw))

            # breakout if we found a match
            if self.operator(tests):
                return True

        # test final match
        return self.operator(tests)

    def _simple_match(self, term, text, raw):
        """
        just check for a term or phrase.
        """
        if term in text:
            return True
        elif term in raw.lower():
            return True
        return False

    def _fuzzy_match(self, term, text):
        """
        Fuzzy match on phrases.
        """
        n = phrase_grams(term)
        for gram in tokenizer(text, n):
            d = jellyfish.jaro_distance(term, gram)
            if d >= self.fuzzy_threshold:
                return True
        return False

    def _regex_match(self, term, text, raw):
        """
        Apply a regex
        """
        if term.search(text):
            return True
        if term.search(raw):
            return True
        return False

    def _process_text(self, text, **kw):
        """
        Preprocess text.
        """
        # always lower case + unidecode
        text = unicode(
            unidecode(text.lower().decode('utf-8')), errors='ignore')

        # optionally remove punctuation
        if kw.get('rm_punct', True):
            text = "".join(map(lambda x: x if x not in punct else " ", text))

        # optionally remove digits
        if kw.get('rm_digits', True):
            text = "".join(map(lambda x: x if x not in digits else " ", text))

        # optionally remove whitespace
        if kw.get('rm_html', True):
            text = html.strip_tags(text)

        # optionally remove whitespace
        if kw.get('rm_whitespace', True):
            text = re_whitespace.sub(" ", text).strip()

        return text
