
from newslynx.lib import dates
from datetime import timedelta
from newslynx.sc import SousChef
from newslynx.lib import shares


class TimeseriesCounts(SousChef):
    timeout = 1000

    def setup(self):
        max_age = self.options.get('max_age')
        self.max_age = dates.now() - timedelta(days=max_age)

    def run(self):
        """
        Count shares for all content items.
        """
        for content_item in self.api.orgs.simple_content():
            created = dates.parse_iso(content_item['created'])
            if created < self.max_age:
                continue
            url = content_item.get('url')
            if url:
                data = shares.count(url)
                data.pop('url', None)
                data['content_item_id'] = content_item.get('id')
                yield data

    def load(self, data):
        status_resp = self.api.content.bulk_create_timeseries(list(data))
        return self.api.jobs.poll(**status_resp)
