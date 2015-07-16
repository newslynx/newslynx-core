from datetime import datetime
import copy
from collections import defaultdict

import googleanalytics as ga

from newslynx.sc import SousChef
from newslynx import settings
from newslynx.lib import dates
from newslynx.lib import url
from newslynx.lib import stats
import pytz


class SCGoogleAnalytics(SousChef):

    def connect(self):

        tokens = self.auths.get('google-analytics', None)
        properties = tokens.pop('properties', [])

        if not tokens:
            raise Exception(
                'You must authenticate with google analytics to use this sous chef.')
        if not len(properties):
            raise Exception(
                'You must specify a list of google analytics properties to track. Try re-authenticating.')

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

        profiles = []

        # search for configured profiles.
        for account in accounts:
            for prop in account.webproperties:
                for p in properties:
                    if not p['property'] == prop.url:
                        continue
                    for prof in prop.profiles:
                        if not prof.name == p['profile']:
                            continue
                        if prof not in profiles:
                            profiles.append(prof)
                            break

        if not len(profiles):
            raise Exception(
                'Could not find active profiles for {}'.format(properties))

        return profiles

    def setup(self):
        """
        Connect to googla analytcs, select properties, get content items.
        """
        self.profiles = self.connect()
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
                p = url.get_path(u)
                if not p or p == "/":
                    p = ""
                self.domain_lookup[domain][p].append(c['id'])
            elif u:
                self.url_lookup[u].append(c['id'])

    def reconcile_urls(self, row, prof):
        """
        This is where the ugly, ugly magic happens.
        """
        domain = row.pop('domain', None)
        path = row.pop('path', None)
        prof_url = prof.raw.get('websiteUrl')

        # get the canonical domain:
        if not domain or 'not set' in domain:
            base = copy.copy(prof_url)

        # absolutify paths with domains.
        elif not path.startswith('/'):
            base = copy.copy(path)
        else:
            base = copy.copy(domain)

        base_url = url.prepare(base, canonicalize=False, expand=False)
        domain = url.get_domain(base_url)

        # standardize with lookup.
        if path == "/":
            path = ""

        # lookup via domain + path.
        if domain in self.domain_lookup and path in self.domain_lookup[domain]:
            for cid in self.domain_lookup.get(domain, {}).get(path, []):
                r = copy.copy(row)
                r['content_item_id'] = cid
                yield r
        else:
            # lookup via full url
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
                for r in self.reconcile_urls(row, prof):
                    yield r

    def load(self, data):
        status_resp = self.api.content.bulk_create_timeseries(list(data))
        return self.api.jobs.poll(**status_resp)


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
        q = prof.core.query(self.METRICS.keys(), self.DIMENSIONS.keys())\
                     .range('2015-06-01', days=90)\
                     .sort(*self.SORT_KEYS)
        r = q.execute()
        return r.rows

    def format_row_names(self, row):
        """
        Rename rows based on metric / dimension lookups.
        """
        new_row = {}
        for k, v in row._asdict().iteritems():
            k = k.replace('_', '').lower().strip()
            if k in self.LOOKUP:
                new_row[self.LOOKUP[k]] = v
            else:
                new_row[k] = v
        return new_row

    def format_date(self, ds, tz=None):
        """
        Convert datehour to utc based on profiles timezone
        """
        if not tz:
            tz = pytz.utc
        dt = datetime.strptime(ds, '%Y%m%d%H')
        dt = dt.replace(tzinfo=tz)
        return dates.convert_to_utc(dt)

    def format(self, data, prof):
        """
        Cleanup numbers, date, and column names.
        """
        # create lookups.
        self.LOOKUP = {k.lower(): v for k, v in self.METRICS.items()}
        self.LOOKUP.update({k.lower(): v for k, v in self.DIMENSIONS.items()})

        # get timezone from profile
        tz = prof.raw.get('timezone', None)
        if tz:
            tz = pytz.timezone(tz)

        # get website url from profile
        prof_url = prof.raw.get('websiteUrl', None)

        # iterate through results and parse.
        for row in data:
            row = self.format_row_names(row)
            # format date
            row['datetime'] = self.format_date(row['datetime'])
            # format numerics
            for k, v in copy.copy(row).items():
                if k not in ['datetime', 'domain', 'path']:
                    row[k] = stats.parse_number(v)
            yield row




class ContentDomainFacets(SousChef):
    pass


class ContentDeviceSummaries(SousChef):
    pass
