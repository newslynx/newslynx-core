"""
All utilities related to regexes and 
a big ugly library of them.

"""
import re

# hack to check for regex type
RE_TYPE = type(re.compile(r''))


def compile_regex(r, flags=None):
    """
    a helper for building a regex or not.
    """
    if isinstance(r, RE_TYPE):
        return r
    else:
        return re.compile(r, flags=flags)

# NAMES #

# regexes
re_name_token = re.compile(r"[^\w\'\-\.]")
re_by = re.compile(r'[bB][yY][\:\s]|[fF]rom[\:\s]')
re_initial = re.compile(r'^([A-Z](\.)?){1,2}$', re.IGNORECASE)
re_digits = re.compile('\d')
re_prefix_suffix = re.compile(r"""
  (^[Dd][Rr](\.)?$)|                   # Dr.
  (^[Mm](\.)?([Dd])(\.)?$)|            # MD
  (^[SsJj][Rr](\.)?$)|                 # SR / JR
  (^[Mm](iss)?([RrSs])?([Ss])?(\.)?$)| # Mr / Ms. / Mrs / Miss
  (^P(\.)?[Hh][Dd](\.)?)|              # PHD
  (^I(\.)?I(\.)?I(\.)?$)|              # III 
  (^I(\.)?V(\.)?$)|                    # IV
  (^V(\.)?$)                            # V
""", re.VERBOSE)


# URLS #

# this regex was brought to you by django!
re_abs_url = re.compile(r"""
  ^(?:http|ftp)s?://                                                                 # http:// or https://
  (?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|  # domain...
  localhost|                                                                         # localhost...
  \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|                                                # ...or ipv4
  \[?[A-F0-9]*:[A-F0-9:]+\]?)                                                        # ...or ipv6
  (?::\d+)?                                                                          # optional port
  (?:/?|[/?]\S+)$
""", flags=re.VERBOSE)

# find a date in a url
re_url_date = re.compile(r"""
  ([\./\-_]{0,1}(19|20)\d{2}) # year
  [\./\-_]{0,1} # separator
  (([0-3]{0,1}[0-9][\./\-_])|(\w{3,5}[\./\-_])) # month/date/section
  ([0-3]{0,1}[0-9][\./\-]{0,1})? # ?
""", flags=re.VERBOSE)

# match a bitly-ish shorturl
re_short_url = re.compile(r"""                   
  ^(                      # start group
    (https?://)?          # optional scheme
    ([a-z1-9]+\.)?        # optional sub domain
    [a-z1-9]+.[a-z1-9]+/  # required domain
    [a-z1-9]{5,9}         # six-ish digit hash
  )$                      # end group
""", re.VERBOSE | re.IGNORECASE)

# match a bitly-ish shorturl in text
re_short_url_text = re.compile(r"""                   
   (                      # start group
    (https?://)           # scheme
    ([a-z1-9]+\.)?        # optional sub domain
    [a-z1-9]+.[a-z1-9]+/  # required domain
    [a-z1-9]{1,12}        # six-ish digit hash
  )                       # end group
""", re.VERBOSE | re.IGNORECASE)

# remove https / http / .html from url for slugging / hashing
re_http = re.compile(r'^http(s)?')
re_html = re.compile(r'(index\.)?htm(l)?$')
re_index_html = re.compile(r'index\.htm(l)?$')
re_www = re.compile(r'^www\.')
re_slug = re.compile(r'[^\sA-Za-z0-9]+')
re_slug_end = re.compile(r'(^[\-]+)|([\-]+)$')
re_url = re.compile(r'https?://[^\s\'\"]+')
re_bitly_warning = re.compile(r'https?://bitly\.com/a/warning')

# a big ugly list of short_urls
re_short_domains = re.compile(r"""
  (^bit\.do$)|
  (^t\.co$)|
  (^go2\.do$)|
  (^adf\.ly$)|
  (^goo\.gl$)|
  (^bitly\.com$)|
  (^bit\.ly$)|
  (^tinyurl\.com$)|
  (^ow\.ly$)|
  (^bit\.ly$)|
  (^adcrun\.ch$)|
  (^zpag\.es$)|
  (^ity\.im$)|
  (^q\.gs$)|
  (^lnk\.co$)|
  (^viralurl\.com$)|
  (^is\.gd$)|
  (^vur\.me$)|
  (^bc\.vc$)|
  (^yu2\.it$)|
  (^twitthis\.com$)|
  (^u\.to$)|
  (^j\.mp$)|
  (^bee4\.biz$)|
  (^adflav\.com$)|
  (^buzurl\.com$)|
  (^xlinkz\.info$)|
  (^cutt\.us$)|
  (^u\.bb$)|
  (^yourls\.org$)|
  (^fun\.ly$)|
  (^hit\.my$)|
  (^nov\.io$)|
  (^crisco\.com$)|
  (^x\.co$)|
  (^shortquik\.com$)|
  (^prettylinkpro\.com$)|
  (^viralurl\.biz$)|
  (^longurl\.org$)|
  (^tota2\.com$)|
  (^adcraft\.co$)|
  (^virl\.ws$)|
  (^scrnch\.me$)|
  (^filoops\.info$)|
  (^linkto\.im$)|
  (^vurl\.bz$)|
  (^fzy\.co$)|
  (^vzturl\.com$)|
  (^picz\.us$)|
  (^lemde\.fr$)|
  (^golinks\.co$)|
  (^xtu\.me$)|
  (^qr\.net$)|
  (^1url\.com$)|
  (^tweez\.me$)|
  (^sk\.gy$)|
  (^gog\.li$)|
  (^cektkp\.com$)|
  (^v\.gd$)|
  (^p6l\.org$)|
  (^id\.tl$)|
  (^dft\.ba$)|
  (^aka\.gr$)|
  (^bbc.in$)|
  (^ift\.tt$)|
  (^amzn.to$)|
  (^p\.tl$)|
  (^trib\.al$)|
  (^1od\.biz$)|
  (^ht\.ly$)|
  (^fb\.me$)|
  (^4sq\.com$)|
  (^tmblr\.co$)|
  (^dlvr\.it$)|
  (^trib\.al$)|
  (^ow\.ly$)|
  (^mojo\.ly$)|
  (^propub\.ca$)|
  (^feeds\.propublica\.org$)|
  (^ckbe\.at$)|
  (^polti\.co$)|
  (^pocket\.co$)|
  (^n\.pr$)|
  (^washpo\.st$)|
  (^nyti\.ms$)|
  (^wrd\.com$)|
  (^nyp\.st$)|
  (^apne\.ws$)|
  (^alj\.am$)|
  (^sbn\.to$)|
  (^lat.ms$)|
  (^fw\.to$)|
  (^abcn\.ws$)|
  (^ampr\.gs$)|
  (^cl\.ly$)|
  (^j\.mp$)|
  (^thkpr\.gs$)|
  (^huff\.to$)|
  (^alj\.am$)
  """, flags=re.VERBOSE | re.IGNORECASE)
