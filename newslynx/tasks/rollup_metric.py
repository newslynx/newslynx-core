"""
Query logic for rollingup timeseries metrics => summary metrics.
"""
from datetime import timedelta

from newslynx.lib.serialize import obj_to_json
from newslynx.exc import NotFoundError, RequestError
from newslynx.core import db
from newslynx.lib import dates
from newslynx.constants import IMPACT_TAG_CATEGORIES, IMPACT_TAG_LEVELS
from newslynx.tasks.query_metric import QueryContentMetricTimeseries
from newslynx.models import Org


def content_timeseries_to_summary(org, content_item_ids=[], num_hours=24):
    """
    Rollup content-timseries metrics into summaries.
    Optimize this query by only updating content items
    which have had updates to their metrics in the last X hours.
    """

    # just use this to generate a giant timeseries select with computed
    # metrics.
    if not len(content_item_ids):
        content_item_ids = org.content_item_ids
    if not len(content_item_ids):
        raise RequestError('You must have content items to run this method.')

    ts = QueryContentMetricTimeseries(org, content_item_ids, unit=None)

    # generate aggregation statments + list of metric names.
    summary_pattern = "{agg}({name}) AS {name}"
    select_statements = []
    metrics = []
    for n, m in org.content_timeseries_metric_rollups.items():
        ss = summary_pattern.format(**m)
        select_statements.append(ss)
        metrics.append(n)

    qkw = {
        'select_statements': ",\n".join(select_statements),
        'metrics': ", ".join(metrics),
        'org_id': org.id,
        'last_updated': (dates.now() - timedelta(hours=num_hours)).isoformat(),
        'ts_query': ts.query
    }

    q = """SELECT upsert_content_metric_summary({org_id}, content_item_id, metrics::text)
           FROM  (
              SELECT
                content_item_id,
                (SELECT row_to_json(_) from (SELECT {metrics}) as _) as metrics
              FROM (
                 SELECT
                    content_item_id,
                    {select_statements}
                FROM ({ts_query}) zzzz
                WHERE content_item_id in (
                    SELECT
                        distinct(content_item_id)
                    FROM content_metric_timeseries
                    WHERE updated > '{last_updated}'
                    )
                GROUP BY content_item_id
                ) t1
            ) t2
        """.format(**qkw)
    db.session.execute(q)
    db.session.commit()
    return True


def event_tags_to_summary(org, content_item_ids=[]):
    """
    Count up impact tag categories + levels assigned to events
    by the content_items they're associated with.
    """
    if not isinstance(content_item_ids, list):
        content_item_ids = [content_item_ids]

    if not len(content_item_ids):
        content_item_ids = org.content_item_ids

    # build up list of metrics to compute
    event_tag_metrics = ['total_events', 'total_event_tags']
    case_statements = []

    case_pattern = """
    sum(CASE WHEN {type} = '{value}'
             THEN 1
             ELSE 0
        END) AS {name}"""

    for l in IMPACT_TAG_LEVELS:
        kw = {
            'type': 'level',
            'value': l,
            'name': "{}_level_events".format(l)
        }
        case_statements.append(case_pattern.format(**kw))
        event_tag_metrics.append(kw['name'])

    for c in IMPACT_TAG_CATEGORIES:
        kw = {
            'type': 'category',
            'value': c,
            'name': "{}_category_events".format(c)
        }
        case_statements.append(case_pattern.format(**kw))
        event_tag_metrics.append(kw['name'])

    content_ids_filter = ""
    if len(content_item_ids):
        content_ids_filter = "AND content_item_id in ({})"\
            .format(",".join([str(i) for i in content_item_ids]))

    # query formatting kwargs
    qkw = {
        "metrics": ", ".join(event_tag_metrics),
        "case_statements": ",\n".join(case_statements),
        "org_id": org.id,
        "null_metrics": obj_to_json({k: 0 for k in event_tag_metrics}),
        "content_ids_filter": content_ids_filter
    }

    # optionally add in null-query
    null_q = """
        -- Content Items With No Approved Events
        , null_metrics AS (
            SELECT upsert_content_metric_summary(t.org_id, t.content_item_id, '{null_metrics}')
            FROM (
                SELECT org_id, id as content_item_id
                FROM content
                WHERE org_id = {org_id} AND
                id NOT IN (
                    SELECT distinct(content_item_id)
                    FROM content_event_metrics
                    )
            ) t
        )
    """.format(**qkw)

    # add in null query if we're not filtering
    # by specific content item ids.
    qkw['null_query'] = ""
    qkw['final_query'] = "select * from positive_metrics"
    if not content_ids_filter:
        qkw['null_query'] = null_q
        qkw['final_query'] = """
            select * from positive_metrics
            UNION ALL
            select * from  null_metrics"""

    q = """
        WITH content_event_tags AS (
            SELECT * FROM
                (
                  SELECT
                    events.id as event_id,
                    events.org_id,
                    content_items_events.content_item_id,
                    tags.category,
                    tags.level from events
                  FULL OUTER JOIN content_items_events on events.id = content_items_events.event_id
                  FULL OUTER JOIN events_tags on events.id = events_tags.event_id
                  FULL OUTER JOIN tags on events_tags.tag_id = tags.id
                  WHERE events.org_id = {org_id} AND
                        events.status = 'approved' AND 
                        (tags.category IS NOT NULL OR tags.level IS NOT NULL)
                ) t
                WHERE content_item_id IS NOT NULL
                {content_ids_filter}
        ),
        content_event_tag_counts AS (
            SELECT
                org_id,
                content_item_id,
                count(distinct(event_id)) as total_events,
                count(1) as total_event_tags,
                {case_statements}
            FROM content_event_tags
            GROUP BY org_id, content_item_id
        ),
        content_event_metrics AS (
            SELECT
                org_id,
                content_item_id,
                (SELECT row_to_json(_) from (SELECT {metrics}) as _) as metrics
            FROM content_event_tag_counts
        ),

        -- Content Items With Approved Events
        positive_metrics AS (
            SELECT
                upsert_content_metric_summary(org_id, content_item_id, metrics::text)
            FROM content_event_metrics
        )
        {null_query}
        {final_query}
        """.format(**qkw)
    db.session.execute(q)
    db.session.commit()
    return True
