from newslynx.core import db

"""INSERT INTO content_metric_summary (org_id, content_item_id, metrics) (
   SELECT
       org_id,
       content_item_id,
      (SELECT row_to_json(_) from (SELECT t.pageviews, t.twitter_shares) as _) as metrics
   FROM (
       SELECT
           org_id,
           content_item_id,
           sum((metrics ->> 'pageviews')::text::numeric) AS pageviews,
           sum((metrics ->> 'twitter_shares')::text::numeric) AS twitter_shares
       FROM content_metric_timeseries GROUP BY content_item_id, org_id
       ) t
)
"""
