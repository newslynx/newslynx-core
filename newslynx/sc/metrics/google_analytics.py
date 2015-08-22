"""
Google Analytics Sous Chefs.
"""

from datetime import datetime, timedelta
import copy
from collections import defaultdict, Counter
from operator import itemgetter

import googleanalytics as ga

from newslynx.sc import SousChef
from newslynx import settings
from newslynx.lib import dates
from newslynx.lib import url
from newslynx.lib import stats
import pytz


class SCGoogleAnalytics(SousChef):

    timeout = 1800

    def connect(self):
        self.profiles = []
        tokens = self.auths.get('google-analytics', None)
        properties = tokens.pop('properties', [])

        if not tokens:
            raise Exception(
                'You must authenticate with google analytics to use this sous chef.')
        if not len(properties):
            raise Exception(
                'You must specify a list of google analytics properties to track. '
                'Try re-authenticating.')

        # authenticate with accounts
        conn_kw = {
            'refresh_token': tokens.get('refresh_token', None),
            'client_id': settings.GOOGLE_ANALYTICS_CLIENT_ID,
            'client_secret': settings.GOOGLE_ANALYTICS_CLIENT_SECRET
        }
        try:
            accounts = ga.authenticate(**conn_kw)
        except Exception as e:
            raise Exception('Error connecting to google analytics: {}'
                            .format(e.message))

        # search for configured profiles.
        for account in accounts:
            for prop in account.webproperties:
                for p in properties:
                    if not p['property'] == prop.url:
                        continue
                    for prof in prop.profiles:
                        print prof.name, p['profile']
                        if not prof.name == p['profile']:
                            continue
                        if prof not in self.profiles:
                            self.profiles.append(prof)
                            break

        if not len(self.profiles):
            raise Exception(
                'Could not find active profiles for {}'.format(properties))

    def setup(self):
        """
        Connect to googla analytcs, select properties, get content items.
        """
        self.connect()
        self._gen_lookups()

    def _gen_lookups(self):
        """
        Create a tree of
        domain => path > content item ids.
        for fast lookups against google analytics urls.

        Fallback to lookup of url > content item ids.

        """
        # create containers
        self.domain_lookup = defaultdict(lambda: defaultdict(list))
        self.url_lookup = defaultdict(list)

        # populate with ALL content items.
        for c in self.api.orgs.simple_content():
            u = c.pop('url', None)
            domain = c.pop('domain', None)
            if u and domain:
                # parse path
                p = url.get_path(u)
                # standardize home domains.
                if p == "" or p == "/":
                    p = "/"
                elif not p:
                    continue
                # build up list of ids.
                self.domain_lookup[domain][p].append(c['id'])
            elif u:
                self.url_lookup[u].append(c['id'])

    def reconcile_urls(self, row, prof):
        """
        This is where the ugly, ugly magic happens.
        """
        domain = row.pop('domain', None)
        path = row.pop('path', None)
        prof_url = prof.raw.get('websiteUrl', None)

        # get the canonical domain:
        base = None
        if not domain or 'not set' in domain:
            if prof_url:
                base = copy.copy(prof_url)

        # absolutify paths with domains.
        elif not path.startswith('/'):
            base = copy.copy(path)

        else:
            base = copy.copy(domain)
        if not base:
            raise Exception('Could not process {}{}'.format(domain, path))

        base_url = url.prepare(base, canonicalize=False, expand=False)
        domain = url.get_domain(base_url)

        # lookup via domain + path.
        found = False
        if domain in self.domain_lookup and path in self.domain_lookup[domain]:
            for cid in self.domain_lookup.get(domain, {}).get(path, []):
                found = True
                r = copy.copy(row)
                r['content_item_id'] = cid
                yield r

        # lookup via full url
        if not found:
            u = url.join(base_url, path)
            for cid in self.url_lookup.get(u, []):
                r = copy.copy(row)
                r['content_item_id'] = cid
                yield r

    def fetch(self, prof):
        pass

    def format(self, data):
        return data

    def run(self):
        for prof in self.profiles:
            data = self.fetch(prof)
            for row in self.format(data, prof):
                yield row


class ContentTimeseries(SCGoogleAnalytics):

    METRICS = {
        'pageviews': 'ga_pageviews',
        'timeOnPage': 'ga_total_time_on_page',
        'exits': 'ga_exits',
        'entrances': 'ga_entrances'
    }

    DIMENSIONS = {
        'hostname': 'domain',
        'pagePath': 'path',
        'dateHour': 'datetime'
    }

    SORT_KEYS = [
        '-dateHour',
        '-pagePath'
    ]

    def fetch(self, prof):
        days = self.options.get('days', 5)
        start = (dates.now() - timedelta(days=days)).date().isoformat()
        i = 1
        while 1:
            q = prof.core.query(self.METRICS.keys(), self.DIMENSIONS.keys())\
                         .range(start, days=days)\
                         .sort(*self.SORT_KEYS)\
                         .limit(i, i+1000)
            self.log.info('Running query:\n\t{}\n\tat limit {}'.format(q.raw, i))
            i += 1000
            r = q.execute()
            if not len(r.rows):
                break
            for row in r.rows:
                yield row

    def format_row_names(self, row):
        """
        Rename rows based on metric / dimension lookups.
        """
        new_row = {}
        for k, v in row._asdict().iteritems():
            k = k.replace('_', '').lower().strip()
            if k in self.col_lookup:
                new_row[self.col_lookup[k]] = v
            else:
                new_row[k] = v
        return new_row

    def format_date(self, ds, tz=None):
        """
        Convert datehour to utc based on the profile's timezone
        """
        if not tz:
            tz = pytz.utc
        dt = datetime.strptime(ds, '%Y%m%d%H')
        dt = dt.replace(tzinfo=tz)
        dt = dates.convert_to_utc(dt)

        # round to nearest hour
        dt += timedelta(minutes=30)
        dt -= timedelta(minutes=dt.minute % 60)
        return dt

    def pre_format(self, data, prof):
        """
        Cleanup numbers, date, and column names.
        """

        # create lookups.
        self.col_lookup = {k.lower(): v for  k, v in self.METRICS.items()}
        self.col_lookup.update({k.lower(): v for k, v in self.DIMENSIONS.items()})

        # get timezone from profile
        tz = prof.raw.get('timezone', None)
        if tz:
            tz = pytz.timezone(tz)

        # iterate through results and parse.
        for row in data:
            row = self.format_row_names(row)

            # format date
            row['datetime'] = self.format_date(row['datetime'], tz=tz)

            # format numerics
            for k, v in copy.copy(row).items():
                if k not in ['datetime', 'domain', 'path']:
                    row[k] = stats.parse_number(v)

            # reconcile urls.
            for r in self.reconcile_urls(row, prof):
                yield r

    def format(self, data, prof):
        """
        because of how we parse the urls, there can be multiple distinct rows of datetime + content_item id.
        normalize them here.
        """
        d = defaultdict(lambda: defaultdict(Counter))

        for r in self.pre_format(data, prof):
            for m, v in r.items():
                if m not in ['content_item_id', 'datetime']:
                    d[r['content_item_id']][r['datetime']][m] += v

        for cid in d.keys():
            for dt in d[cid].keys():
                metrics = dict(d[cid].get(dt, {}))
                metrics.update({'content_item_id': cid, 'datetime': dt})
                yield metrics

    def load(self, data):
        d = list(data)
        status_resp = self.api.content.bulk_create_timeseries(data=d)
        return self.api.jobs.poll(**status_resp)

# class ContentDomainFacets(SousChef):
#     pass


class ContentDomainFacets(SCGoogleAnalytics):

    METRICS = {
        'pageviews': 'pageviews',
    }

    DIMENSIONS = {
        'hostname': 'domain',
        'pagePath': 'path',
        'fullReferrer': 'referrer'
    }

    SEARCH_REFERRERS = [
        'google', 'bing', 'ask', 'aol',
        'yahoo', 'comcast', 'search-results',
        'disqus', 'cnn', 'aol', 'baidu'
    ]

    def parse_referrer(self, row):
        """
        Parse a referrer.
        """
        referrer = row.get('referrer')

        if referrer == "(not set)":
            row['referrer'] = 'null'
            row['ref_domain'] = 'null'

        elif referrer == "(direct)":
            row['referrer'] = 'direct'
            row['ref_domain'] = 'direct'

        elif referrer in self.SEARCH_REFERRERS:
            row['referrer'] = referrer
            row['ref_domain'] = referrer

        # special handling.
        elif 't.co' in referrer:
            row['referrer'] = url.prepare(referrer, expand=False, canonicalize=False)
            row['ref_domain'] = 'twitter'

        elif 'facebook' in referrer:
            row['referrer'] = url.prepare(referrer, expand=False, canonicalize=False)
            row['ref_domain'] = 'facebook'

        else:
            row['referrer'] = url.prepare(referrer, expand=False, canonicalize=False)
            row['ref_domain'] = url.get_simple_domain(row['referrer'])

        return row

    def fetch(self, prof):
        days = self.options.get('days', 30)
        start = (dates.now() - timedelta(days=days)).date().isoformat()
        i = 1
        while 1:
            q = prof.core.query(self.METRICS.keys(), self.DIMENSIONS.keys())\
                         .range(start, days=days)\
                         .limit(i, i+1000)
            self.log.info('Running query:\n\t{}\n\tat limit {}'.format(q.raw, i))
            i += 1000
            r = q.execute()
            # pause in between queries.
            time.sleep(5)

            if not len(r.rows):
                break
            for row in r.rows:
                yield row

    def format_row_names(self, row):
        """
        Rename rows based on metric / dimension lookups.
        """
        new_row = {}
        for k, v in row._asdict().iteritems():
            k = k.replace('_', '').lower().strip()
            if k in self.col_lookup:
                new_row[self.col_lookup[k]] = v
            else:
                new_row[k] = v
        return new_row

    def pre_format(self, data, prof):
        """
        Parse + reconcile
        """
        self.col_lookup = {k.lower(): v for k, v in self.METRICS.items()}
        self.col_lookup.update({k.lower(): v for k, v in self.DIMENSIONS.items()})
        for row in data:
            row = self.format_row_names(row)
            row = self.parse_referrer(row)
            row['pageviews'] = stats.parse_number(row.get('pageviews', 0))
            for r in self.reconcile_urls(row, prof):
                yield r

    def format(self, data, prof):

        # build up facets.
        facets = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        for row in self.pre_format(data, prof):
            cid = row['content_item_id']
            facets[cid]['ga_pageviews_by_domain'][row['ref_domain']] \
                += row['pageviews']
            if url.is_article(row['referrer']):
                facets[cid]['ga_pageviews_by_article_referrer'][row['referrer']] \
                    += row['pageviews']

        # format into newslnyx facets.
        for cid, value in dict(facets).iteritems():
            row = {'content_item_id': cid}
            for metric, _facets in value.iteritems():
                row[metric] = []
                n_facets = 0
                for k, v in sorted(_facets.iteritems(), key=itemgetter(1), reverse=True):
                    n_facets += 1
                    if n_facets >= self.options['max_facets']:
                        break
                    row[metric].append({'facet': k, 'value': v})
            yield row

    def load(self, data):
        """
        Load 
        """
        d = list(data)
        status_resp = self.api.content.bulk_create_summary(data=d)
        return self.api.jobs.poll(**status_resp)


class ContentDeviceSummaries(SCGoogleAnalytics):

    METRICS = {
        'pageviews': 'pageviews'
    }

    DIMENSIONS = {
        'hostname': 'domain',
        'pagePath': 'path',
        'deviceCategory': 'device'
    }

    def fetch(self, prof):
        days = self.options.get('days', 30)
        start = (dates.now() - timedelta(days=days)).date().isoformat()
        i = 1
        while 1:
            q = prof.core.query(self.METRICS.keys(), self.DIMENSIONS.keys())\
                         .range(start, days=days)\
                         .limit(i, i+1000)
            self.log.info('Running query:\n\t{}\n\tat limit {}'.format(q.raw, i))
            i += 1000
            r = q.execute()
            if not len(r.rows):
                break
            for row in r.rows:
                yield row

    def format_row_names(self, row):
        """
        Rename rows based on metric / dimension lookups.
        """
        new_row = {}
        for k, v in row._asdict().iteritems():
            k = k.replace('_', '').lower().strip()
            if k in self.col_lookup:
                new_row[self.col_lookup[k]] = v
            else:
                new_row[k] = v
        return new_row

    def pre_format(self, data, prof):
        """
        Lookup content item ids.
        """
        # create lookups.
        self.col_lookup = {k.lower(): v for k, v in self.METRICS.items()}
        self.col_lookup.update({k.lower(): v for k, v in self.DIMENSIONS.items()})
        for row in data:
            row = self.format_row_names(row)
            row['device'] = row['device'].lower()
            for r in self.reconcile_urls(row, prof):
                yield r

    def format(self, data, prof):

        # group counts.
        counts = defaultdict(Counter)
        for row in self.pre_format(data, prof):
            counts[row['content_item_id']][row['device']] += row.get('pageviews', 0)

        for cid, facets in counts.iteritems():
            row = {'content_item_id': cid}

            # fill in zeros.
            for k in ['mobile', 'desktop', 'tablet']:
                if k not in facets:
                    facets[k] = 0

            # populate metrics.
            for k in ['mobile', 'desktop', 'tablet']:
                row['ga_pageviews_'+k] = stats.parse_number(facets[k])

            yield row

    def load(self, data):
        d = list(data)
        status_resp = self.api.content.bulk_create_summary(data=d)
        return self.api.jobs.poll(**status_resp)
