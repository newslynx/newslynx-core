from newslynx.sc import SousChef

from newslynx.lib import rss
from newslynx.lib import dates
from newslynx.lib import url


class Article(SousChef):
    timeout = 240
    extract = True

    def setup(self):
        # get max publish date of the last time we ran this.
        max_date_last_run = self.last_job.get('max_date_last_run', None)
        if max_date_last_run:
            self.max_date_last_run = dates.parse_iso(max_date_last_run)
        else:
            self.max_date_last_run = None
        self.publish_dates = []

    def run(self):
        """
        Extract an RSS Feed and create articles.
        """
        feed_url = self.options['feed_url']
        feed_domain = url.get_simple_domain(feed_url)
        domains = self.org.get('domains', [''])
        if feed_domain:
            domains.append(feed_domain)

        # iterate through RSS entries.
        for article in rss.get_entries(feed_url, domains):
            article['type'] = 'article'  # set this type as article.

            # since we poll often, we can assume this is a good
            # approximation of an article publish date.
            if not article.get('created'):
                article['created'] = dates.now()

            # if we havent run, just yield all results.
            if not self.max_date_last_run:
                self.publish_dates.append(article['created'])
                yield article

            # only yield new articles
            elif article['created'] > self.max_date_last_run:
                self.publish_dates.append(article['created'])
                yield article

    def load(self, data):
        status_resp = self.api.content.bulk_create(
            data=list(data), recipe_id=self.recipe_id)
        return self.api.jobs.poll(**status_resp)

    def teardown(self):
        if len(self.publish_dates):
            max_date_last_run = max(self.publish_dates).isoformat()
            self.next_job['max_date_last_run'] = max_date_last_run
