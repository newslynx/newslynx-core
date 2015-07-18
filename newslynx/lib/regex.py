"""
A big ugly library of regexes
"""

import re

# hack to check for regex type
RE_TYPE = type(re.compile(r''))

# ETC #
re_whitespace = re.compile(r'\n|\t|\r|\s+')

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

# DATES

# a regex for parsing time of day (IE 12:00 AM, 12:00PM)
# to a datetime.time object
re_time = re.compile(r'([0-9]{1,2}):([0-9]{1,2}) (AM|PM)')

# URLS #
re_known_tld = re.compile(r"abb|abbott|abogado|ac|academy|accenture|accountant|accountants|active|actor|ad|ads|adult|ae|aero|af|afl|ag|agency|ai|aig|airforce|al|allfinanz|alsace|am|amsterdam|an|android|ao|apartments|aq|aquarelle|ar|archi|army|arpa|as|asia|associates|at|attorney|au|auction|audio|auto|autos|aw|ax|axa|az|ba|band|bank|bar|barclaycard|barclays|bargains|bauhaus|bayern|bb|bbc|bbva|bd|be|beer|berlin|best|bf|bg|bh|bi|bible|bid|bike|bingo|bio|biz|bj|black|blackfriday|bloomberg|blue|bm|bmw|bn|bnpparibas|bo|boats|bond|boo|boutique|br|bridgestone|broker|brother|brussels|bs|bt|budapest|build|builders|business|buzz|bv|bw|by|bz|bzh|ca|cab|cafe|cal|camera|camp|cancerresearch|canon|capetown|capital|caravan|cards|care|career|careers|cars|cartier|casa|cash|casino|cat|catering|cbn|cc|cd|center|ceo|cern|cf|cfa|cfd|cg|ch|channel|chat|cheap|chloe|christmas|chrome|church|ci|cisco|citic|city|ck|cl|claims|cleaning|click|clinic|clothing|club|cm|cn|co|coach|codes|coffee|college|cologne|com|community|company|computer|condos|construction|consulting|contractors|cooking|cool|coop|corsica|country|coupons|courses|cr|credit|creditcard|cricket|crs|cruises|cu|cuisinella|cv|cw|cx|cy|cz|cymru|cyou|cz|dabur|dad|dance|date|dating|datsun|day|dclk|de|deals|degree|delivery|democrat|dental|dentist|desi|design|dev|diamonds|diet|digital|direct|directory|discount|dj|dk|dm|dnp|do|docs|dog|doha|domains|doosan|download|durban|dvag|dz|earth|eat|ec|edu|education|ee|eg|email|emerck|energy|engineer|engineering|enterprises|epson|equipment|er|erni|es|esq|estate|et|eu|eurovision|eus|events|everbank|exchange|expert|exposed|express|fail|faith|fan|fans|farm|fashion|feedback|fi|film|finance|financial|firmdale|fish|fishing|fit|fitness|fj|fk|flights|florist|flowers|flsmidth|fly|fm|fo|foo|football|forex|forsale|foundation|fr|frl|frogans|fund|furniture|futbol|fyi|ga|gal|gallery|garden|gb|gbiz|gd|gdn|ge|gent|gf|gg|ggee|gh|gi|gift|gifts|gives|gl|glass|gle|global|globo|gm|gmail|gmo|gmx|gn|gold|goldpoint|golf|goo|goog|google|gop|gov|gp|gq|gr|graphics|gratis|green|gripe|gs|gt|gu|guge|guide|guitars|guru|gw|gy|hamburg|hangout|haus|healthcare|help|here|hermes|hiphop|hitachi|hiv|hk|hm|hn|hockey|holdings|holiday|homedepot|homes|honda|horse|host|hosting|house|how|hr|ht|hu|ibm|icbc|icu|id|ie|ifm|il|im|immo|immobilien|in|industries|infiniti|info|ing|ink|institute|insure|int|international|investments|io|iq|ir|irish|is|it|iwc|java|jcb|je|jetzt|jewelry|jll|jm|jo|jobs|joburg|jp|juegos|kaufen|kddi|ke|kg|kh|ki|kim|kitchen|kiwi|km|kn|koeln|komatsu|kp|kr|krd|kred|kw|ky|kyoto|kz|la|lacaixa|land|lat|latrobe|lawyer|lb|lc|lds|lease|leclerc|legal|lgbt|li|liaison|lidl|life|lighting|limited|limo|link|lk|loan|loans|lol|london|lotte|lotto|love|lr|ls|lt|ltda|lu|lupin|luxe|luxury|lv|ly|ma|madrid|maif|maison|management|mango|market|marketing|markets|marriott|mba|mc|md|me|media|meet|melbourne|meme|memorial|men|menu|mg|mh|miami|mil|mini|mk|ml|mm|mma|mn|mo|mobi|moda|moe|monash|money|mormon|mortgage|moscow|motorcycles|mov|movie|mp|mq|mr|ms|mt|mtn|mtpc|mu|museum|mv|mw|mx|my|mz|na|nadex|nagoya|name|navy|nc|ne|nec|net|network|neustar|new|news|nexus|nf|ng|ngo|nhk|ni|nico|ninja|nissan|nl|no|np|nr|nra|nrw|ntt|nu|nyc|nz|okinawa|om|one|ong|onl|online|ooo|oracle|org|organic|osaka|otsuka|ovh|pa|page|panerai|paris|partners|parts|party|pe|pf|pg|ph|pharmacy|philips|photo|photography|photos|physio|piaget|pics|pictet|pictures|pink|pizza|pk|pl|place|plumbing|plus|pm|pn|pohl|poker|porn|post|pr|praxi|press|pro|prod|productions|prof|properties|property|ps|pt|pub|pw|py|qa|qpon|quebec|racing|re|realtor|recipes|red|redstone|rehab|reise|reisen|reit|ren|rent|rentals|repair|report|republican|rest|restaurant|review|reviews|rich|rio|rip|ro|rocks|rodeo|rs|rsvp|ru|ruhr|run|rw|ryukyu|sa|saarland|sale|samsung|sandvik|sandvikcoromant|sap|sarl|saxo|sb|sc|sca|scb|schmidt|scholarships|school|schule|schwarz|science|scot|sd|se|seat|sener|services|sew|sex|sexy|sg|sh|shiksha|shoes|show|shriram|si|singles|site|sj|sk|ski|sky|sl|sm|sn|sncf|so|soccer|social|software|sohu|solar|solutions|sony|soy|space|spiegel|spreadbetting|sr|st|study|style|su|sucks|supplies|supply|support|surf|surgery|suzuki|sv|swiss|sx|sy|sydney|systems|sz|taipei|tatar|tattoo|tax|taxi|tc|td|team|tech|technology|tel|temasek|tennis|tf|tg|th|thd|theater|tickets|tienda|tips|tires|tirol|tj|tk|tl|tm|tn|to|today|tokyo|tools|top|toray|toshiba|tours|town|toys|tr|trade|trading|training|travel|trust|tt|tui|tv|tw|tz|ua|ug|uk|university|uno|uol|us|uy|uz|va|vacations|vc|ve|vegas|ventures|versicherung|vet|vg|vi|viajes|video|villas|vision|vlaanderen|vn|vodka|vote|voting|voto|voyage|vu|wales|walter|wang|watch|webcam|website|wed|wedding|weir|wf|whoswho|wien|wiki|williamhill|win|wme|work|works|world|ws|wtc|wtf|xbox|xerox|xin|xxx|xyz|yachts|yandex|ye|yodobashi|yoga|yokohama|youtube|yt|za|zip|zm|zone|zuerich|z")

# find a date in a url
re_url_date = re.compile(r"""
  ([\./\-_]{0,1}(19|20)\d{2}) # year
  [\./\-_]{0,1} # separator
  (([0-3]{0,1}[0-9][\./\-_])|(\w{3,5}[\./\-_])) # month/date/section
  ([0-3]{0,1}[0-9][\./\-]{0,1})? # ?
""", flags=re.VERBOSE)

# match a bitly-ish shorturl
re_short_url = re.compile(r"""
   ^(                     # start group
      (https?://)?        # optional scheme
      ([a-z0-9]+\.)?      # optional sub domain
      [a-z0-9]+\.         # required domain
      (abb|abbott|abogado|ac|academy|accenture|accountant|accountants|active|actor|ad|ads|adult|ae|aero|af|afl|ag|agency|ai|aig|airforce|al|allfinanz|alsace|am|amsterdam|an|android|ao|apartments|aq|aquarelle|ar|archi|army|arpa|as|asia|associates|at|attorney|au|auction|audio|auto|autos|aw|ax|axa|az|ba|band|bank|bar|barclaycard|barclays|bargains|bauhaus|bayern|bb|bbc|bbva|bd|be|beer|berlin|best|bf|bg|bh|bi|bible|bid|bike|bingo|bio|biz|bj|black|blackfriday|bloomberg|blue|bm|bmw|bn|bnpparibas|bo|boats|bond|boo|boutique|br|bridgestone|broker|brother|brussels|bs|bt|budapest|build|builders|business|buzz|bv|bw|by|bz|bzh|ca|cab|cafe|cal|camera|camp|cancerresearch|canon|capetown|capital|caravan|cards|care|career|careers|cars|cartier|casa|cash|casino|cat|catering|cbn|cc|cd|center|ceo|cern|cf|cfa|cfd|cg|ch|channel|chat|cheap|chloe|christmas|chrome|church|ci|cisco|citic|city|ck|cl|claims|cleaning|click|clinic|clothing|club|cm|cn|co|coach|codes|coffee|college|cologne|com|community|company|computer|condos|construction|consulting|contractors|cooking|cool|coop|corsica|country|coupons|courses|cr|credit|creditcard|cricket|crs|cruises|cu|cuisinella|cv|cw|cx|cy|cz|cymru|cyou|cz|dabur|dad|dance|date|dating|datsun|day|dclk|de|deals|degree|delivery|democrat|dental|dentist|desi|design|dev|diamonds|diet|digital|direct|directory|discount|dj|dk|dm|dnp|do|docs|dog|doha|domains|doosan|download|durban|dvag|dz|earth|eat|ec|edu|education|ee|eg|email|emerck|energy|engineer|engineering|enterprises|epson|equipment|er|erni|es|esq|estate|et|eu|eurovision|eus|events|everbank|exchange|expert|exposed|express|fail|faith|fan|fans|farm|fashion|feedback|fi|film|finance|financial|firmdale|fish|fishing|fit|fitness|fj|fk|flights|florist|flowers|flsmidth|fly|fm|fo|foo|football|forex|forsale|foundation|fr|frl|frogans|fund|furniture|futbol|fyi|ga|gal|gallery|garden|gb|gbiz|gd|gdn|ge|gent|gf|gg|ggee|gh|gi|gift|gifts|gives|gl|glass|gle|global|globo|gm|gmail|gmo|gmx|gn|gold|goldpoint|golf|goo|goog|google|gop|gov|gp|gq|gr|graphics|gratis|green|gripe|gs|gt|gu|guge|guide|guitars|guru|gw|gy|hamburg|hangout|haus|healthcare|help|here|hermes|hiphop|hitachi|hiv|hk|hm|hn|hockey|holdings|holiday|homedepot|homes|honda|horse|host|hosting|house|how|hr|ht|hu|ibm|icbc|icu|id|ie|ifm|il|im|immo|immobilien|in|industries|infiniti|info|ing|ink|institute|insure|int|international|investments|io|iq|ir|irish|is|it|iwc|java|jcb|je|jetzt|jewelry|jll|jm|jo|jobs|joburg|jp|juegos|kaufen|kddi|ke|kg|kh|ki|kim|kitchen|kiwi|km|kn|koeln|komatsu|kp|kr|krd|kred|kw|ky|kyoto|kz|la|lacaixa|land|lat|latrobe|lawyer|lb|lc|lds|lease|leclerc|legal|lgbt|li|liaison|lidl|life|lighting|limited|limo|link|lk|loan|loans|lol|london|lotte|lotto|love|lr|ls|lt|ltda|lu|lupin|luxe|luxury|lv|ly|ma|madrid|maif|maison|management|mango|market|marketing|markets|marriott|mba|mc|md|me|media|meet|melbourne|meme|memorial|men|menu|mg|mh|miami|mil|mini|mk|ml|mm|mma|mn|mo|mobi|moda|moe|monash|money|mormon|mortgage|moscow|motorcycles|mov|movie|mp|mq|mr|ms|mt|mtn|mtpc|mu|museum|mv|mw|mx|my|mz|na|nadex|nagoya|name|navy|nc|ne|nec|net|network|neustar|new|news|nexus|nf|ng|ngo|nhk|ni|nico|ninja|nissan|nl|no|np|nr|nra|nrw|ntt|nu|nyc|nz|okinawa|om|one|ong|onl|online|ooo|oracle|org|organic|osaka|otsuka|ovh|pa|page|panerai|paris|partners|parts|party|pe|pf|pg|ph|pharmacy|philips|photo|photography|photos|physio|piaget|pics|pictet|pictures|pink|pizza|pk|pl|place|plumbing|plus|pm|pn|pohl|poker|porn|post|pr|praxi|press|pro|prod|productions|prof|properties|property|ps|pt|pub|pw|py|qa|qpon|quebec|racing|re|realtor|recipes|red|redstone|rehab|reise|reisen|reit|ren|rent|rentals|repair|report|republican|rest|restaurant|review|reviews|rich|rio|rip|ro|rocks|rodeo|rs|rsvp|ru|ruhr|run|rw|ryukyu|sa|saarland|sale|samsung|sandvik|sandvikcoromant|sap|sarl|saxo|sb|sc|sca|scb|schmidt|scholarships|school|schule|schwarz|science|scot|sd|se|seat|sener|services|sew|sex|sexy|sg|sh|shiksha|shoes|show|shriram|si|singles|site|sj|sk|ski|sky|sl|sm|sn|sncf|so|soccer|social|software|sohu|solar|solutions|sony|soy|space|spiegel|spreadbetting|sr|st|study|style|su|sucks|supplies|supply|support|surf|surgery|suzuki|sv|swiss|sx|sy|sydney|systems|sz|taipei|tatar|tattoo|tax|taxi|tc|td|team|tech|technology|tel|temasek|tennis|tf|tg|th|thd|theater|tickets|tienda|tips|tires|tirol|tj|tk|tl|tm|tn|to|today|tokyo|tools|top|toray|toshiba|tours|town|toys|tr|trade|trading|training|travel|trust|tt|tui|tv|tw|tz|ua|ug|uk|university|uno|uol|us|uy|uz|va|vacations|vc|ve|vegas|ventures|versicherung|vet|vg|vi|viajes|video|villas|vision|vlaanderen|vn|vodka|vote|voting|voto|voyage|vu|wales|walter|wang|watch|webcam|website|wed|wedding|weir|wf|whoswho|wien|wiki|williamhill|win|wme|work|works|world|ws|wtc|wtf|xbox|xerox|xin|xxx|xyz|yachts|yandex|ye|yodobashi|yoga|yokohama|youtube|yt|za|zip|zm|zone|zuerich|z)
      /                   # slash
      [a-z0-9\_\-]{1,12}      # six-ish digit hash
    )$                    # end group
""", re.VERBOSE | re.IGNORECASE)

# match a bitly-ish shorturl in text
re_short_url_text = re.compile(r"""
   (                       # start group
     (https?://)?          # scheme
     ([a-z0-9]+\.)?        # optional sub domain
     [a-z0-9\_\-]+\.           # required domain
     (abb|abbott|abogado|ac|academy|accenture|accountant|accountants|active|actor|ad|ads|adult|ae|aero|af|afl|ag|agency|ai|aig|airforce|al|allfinanz|alsace|am|amsterdam|an|android|ao|apartments|aq|aquarelle|ar|archi|army|arpa|as|asia|associates|at|attorney|au|auction|audio|auto|autos|aw|ax|axa|az|ba|band|bank|bar|barclaycard|barclays|bargains|bauhaus|bayern|bb|bbc|bbva|bd|be|beer|berlin|best|bf|bg|bh|bi|bible|bid|bike|bingo|bio|biz|bj|black|blackfriday|bloomberg|blue|bm|bmw|bn|bnpparibas|bo|boats|bond|boo|boutique|br|bridgestone|broker|brother|brussels|bs|bt|budapest|build|builders|business|buzz|bv|bw|by|bz|bzh|ca|cab|cafe|cal|camera|camp|cancerresearch|canon|capetown|capital|caravan|cards|care|career|careers|cars|cartier|casa|cash|casino|cat|catering|cbn|cc|cd|center|ceo|cern|cf|cfa|cfd|cg|ch|channel|chat|cheap|chloe|christmas|chrome|church|ci|cisco|citic|city|ck|cl|claims|cleaning|click|clinic|clothing|club|cm|cn|co|coach|codes|coffee|college|cologne|com|community|company|computer|condos|construction|consulting|contractors|cooking|cool|coop|corsica|country|coupons|courses|cr|credit|creditcard|cricket|crs|cruises|cu|cuisinella|cv|cw|cx|cy|cz|cymru|cyou|cz|dabur|dad|dance|date|dating|datsun|day|dclk|de|deals|degree|delivery|democrat|dental|dentist|desi|design|dev|diamonds|diet|digital|direct|directory|discount|dj|dk|dm|dnp|do|docs|dog|doha|domains|doosan|download|durban|dvag|dz|earth|eat|ec|edu|education|ee|eg|email|emerck|energy|engineer|engineering|enterprises|epson|equipment|er|erni|es|esq|estate|et|eu|eurovision|eus|events|everbank|exchange|expert|exposed|express|fail|faith|fan|fans|farm|fashion|feedback|fi|film|finance|financial|firmdale|fish|fishing|fit|fitness|fj|fk|flights|florist|flowers|flsmidth|fly|fm|fo|foo|football|forex|forsale|foundation|fr|frl|frogans|fund|furniture|futbol|fyi|ga|gal|gallery|garden|gb|gbiz|gd|gdn|ge|gent|gf|gg|ggee|gh|gi|gift|gifts|gives|gl|glass|gle|global|globo|gm|gmail|gmo|gmx|gn|gold|goldpoint|golf|goo|goog|google|gop|gov|gp|gq|gr|graphics|gratis|green|gripe|gs|gt|gu|guge|guide|guitars|guru|gw|gy|hamburg|hangout|haus|healthcare|help|here|hermes|hiphop|hitachi|hiv|hk|hm|hn|hockey|holdings|holiday|homedepot|homes|honda|horse|host|hosting|house|how|hr|ht|hu|ibm|icbc|icu|id|ie|ifm|il|im|immo|immobilien|in|industries|infiniti|info|ing|ink|institute|insure|int|international|investments|io|iq|ir|irish|is|it|iwc|java|jcb|je|jetzt|jewelry|jll|jm|jo|jobs|joburg|jp|juegos|kaufen|kddi|ke|kg|kh|ki|kim|kitchen|kiwi|km|kn|koeln|komatsu|kp|kr|krd|kred|kw|ky|kyoto|kz|la|lacaixa|land|lat|latrobe|lawyer|lb|lc|lds|lease|leclerc|legal|lgbt|li|liaison|lidl|life|lighting|limited|limo|link|lk|loan|loans|lol|london|lotte|lotto|love|lr|ls|lt|ltda|lu|lupin|luxe|luxury|lv|ly|ma|madrid|maif|maison|management|mango|market|marketing|markets|marriott|mba|mc|md|me|media|meet|melbourne|meme|memorial|men|menu|mg|mh|miami|mil|mini|mk|ml|mm|mma|mn|mo|mobi|moda|moe|monash|money|mormon|mortgage|moscow|motorcycles|mov|movie|mp|mq|mr|ms|mt|mtn|mtpc|mu|museum|mv|mw|mx|my|mz|na|nadex|nagoya|name|navy|nc|ne|nec|net|network|neustar|new|news|nexus|nf|ng|ngo|nhk|ni|nico|ninja|nissan|nl|no|np|nr|nra|nrw|ntt|nu|nyc|nz|okinawa|om|one|ong|onl|online|ooo|oracle|org|organic|osaka|otsuka|ovh|pa|page|panerai|paris|partners|parts|party|pe|pf|pg|ph|pharmacy|philips|photo|photography|photos|physio|piaget|pics|pictet|pictures|pink|pizza|pk|pl|place|plumbing|plus|pm|pn|pohl|poker|porn|post|pr|praxi|press|pro|prod|productions|prof|properties|property|ps|pt|pub|pw|py|qa|qpon|quebec|racing|re|realtor|recipes|red|redstone|rehab|reise|reisen|reit|ren|rent|rentals|repair|report|republican|rest|restaurant|review|reviews|rich|rio|rip|ro|rocks|rodeo|rs|rsvp|ru|ruhr|run|rw|ryukyu|sa|saarland|sale|samsung|sandvik|sandvikcoromant|sap|sarl|saxo|sb|sc|sca|scb|schmidt|scholarships|school|schule|schwarz|science|scot|sd|se|seat|sener|services|sew|sex|sexy|sg|sh|shiksha|shoes|show|shriram|si|singles|site|sj|sk|ski|sky|sl|sm|sn|sncf|so|soccer|social|software|sohu|solar|solutions|sony|soy|space|spiegel|spreadbetting|sr|st|study|style|su|sucks|supplies|supply|support|surf|surgery|suzuki|sv|swiss|sx|sy|sydney|systems|sz|taipei|tatar|tattoo|tax|taxi|tc|td|team|tech|technology|tel|temasek|tennis|tf|tg|th|thd|theater|tickets|tienda|tips|tires|tirol|tj|tk|tl|tm|tn|to|today|tokyo|tools|top|toray|toshiba|tours|town|toys|tr|trade|trading|training|travel|trust|tt|tui|tv|tw|tz|ua|ug|uk|university|uno|uol|us|uy|uz|va|vacations|vc|ve|vegas|ventures|versicherung|vet|vg|vi|viajes|video|villas|vision|vlaanderen|vn|vodka|vote|voting|voto|voyage|vu|wales|walter|wang|watch|webcam|website|wed|wedding|weir|wf|whoswho|wien|wiki|williamhill|win|wme|work|works|world|ws|wtc|wtf|xbox|xerox|xin|xxx|xyz|yachts|yandex|ye|yodobashi|yoga|yokohama|youtube|yt|za|zip|zm|zone|zuerich|z)
     /                     # slash
     [^\s.,\?\!\'\"\|\+]{1,12}     # six-ish digit hash
   )                       # end group
""", re.VERBOSE | re.IGNORECASE)

# remove https / http / .html from url for slugging / hashing
re_http = re.compile(r'^http(s)?')
re_html = re.compile(r'(index\.)?htm(l)?$')
re_index_html = re.compile(r'index\.htm(l)?$')
re_www = re.compile(r'www\.')
re_slug = re.compile(r'[^\sA-Za-z0-9]+')
re_slug_end = re.compile(r'(^[\-]+)|([\-]+)$')
re_url = re.compile(r'https?://[^\s\'\"]+')
re_bitly_warning = re.compile(r'(https?://bitly\.com/a/warning)|(http?://bit.ly/a/warning)')

# a big ugly list of known short domains
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
  (^tw\.gs$)|
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
  (^1\.usa\.gov$)|
  (^propub\.ca$)|
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
