from datetime import timedelta

from newslynx.sc import SousChef
from newslynx.lib import dates


class RefreshContentSummaryMetrics(SousChef):
    
    timeout = 720 
    
    def run(self):
        res = self.api.content.refresh_summaries()
        assert(res.get('success', False))


class RefreshContentComparisons(SousChef):
    
    timeout = 720 
    
    def run(self):
        res = self.api.content.refresh_comparisons()
        assert(res.get('success', False))


class DeleteOldEvents(SousChef):
    
    timeout = 720 
    
    def run(self):
        d = dates.now() - timedelta(days=self.options.get('days', 7))
        results = self.api.events.search(
            statuses='deleted',
            updated_before=d.isoformat(),
            per_page=100,
            fields='id')

        for event in results.get('events', []):
            self.api.events.delete(event['id'], force=True)
