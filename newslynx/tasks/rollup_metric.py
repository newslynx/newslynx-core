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


# short cuts 
def all(org, content_item_ids=[], num_hours=24):
    """
    Rollup all metrics.
    """
    content_summary(org, content_item_ids, num_hours)
    org_timeseries(org)
    org_summary(org)
    return True


def content_summary(org, content_item_ids=[], num_hours=24):
    """
    Rollup content summary metrics.
    """
    if not len(content_item_ids):
        content_item_ids = org.content_item_ids
    content_summary_from_events(org, content_item_ids)
    content_summary_from_content_timeseries(org, content_item_ids, num_hours)
    return True


def org_timeseries(org):
    """
    Rollup content timeseries => org timeseries.
    """
    org_timeseries_from_content_timeseries(org)
    return True


def org_summary(org):
    """
    Rollup org timeseries => org summary & content summary => org summary
    """
    org_summary_from_content_summary(org)
    org_summary_from_org_timeseries(org)
    return True


def content_summary_from_content_timeseries(org, content_item_ids=[], num_hours=24):
    """
    Rollup content-timseries metrics into summaries.
    Optimize this query by only updating content items
    which have had updates to their metrics in the last X hours.
    """

    # just use this to generate a giant timeseries select with computed
    # metrics.
    ts = QueryContentMetricTimeseries(org, content_item_ids, unit=None)

    metrics, ss = summary_select(org.content_timeseries_metric_rollups)

    qkw = {
        'select_statements': ss,
        'metrics': metrics,
        'org_id': org.id,
        'last_updated': (dates.now() - timedelta(hours=num_hours)).isoformat(),
        'ts_query': ts.query,
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
                WHERE zzzz.content_item_id in (
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


def content_summary_from_events(org, content_item_ids=[]):
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


def org_timeseries_from_content_timeseries(org):
    """
    Rollup content timeseries => org timeseries.
    """
    # summarize the content timeseries table
    content_ts = QueryContentMetricTimeseries(org, org.content_item_ids,
                                              unit='hour', group_by_id=False)

    # select statements.
    metrics, ss = summary_select(org.timeseries_metric_rollups)

    qkw = {
        'org_id': org.id,
        'metrics': metrics,
        'select_statements': ss,
        'ts_query': content_ts.qu
    }

    # generate the query
    q = \
        """SELECT upsert_org_metric_timeseries({org_id}, datetime, metrics::text)
           FROM  (
              SELECT
                datetime,
                (SELECT row_to_json(_) from (SELECT {metrics}) as _) as metrics
              FROM (
                 SELECT
                    {select_statements}
                FROM ({ts_query}) zzzz
                ) t1
            ) t2
    """.format(**qkw)
    print q
    db.session.execute(q)
    db.session.commit()
    return True


def org_summary_from_content_summary(org):
    """
    Rollup content summary => org summary.
    """

    metrics, ss = summary_select(org.summary_metric_rollups)

    qkw = {
        'select_statements': ss,
        'metrics': metrics,
        'org_id': org.id
    }

    q = \
        """SELECT upsert_org_metric_summary({org_id}, metrics::text)
           FROM  (
              SELECT
                (SELECT row_to_json(_) from (SELECT {metrics}) as _) as metrics
              FROM (
                SELECT
                    {select_statements}
                FROM content_metric_summary
                WHERE org_id = {org_id}
                GROUP BY org_id
                ) t1
            ) t2
        """.format(**qkw)


def org_summary_from_org_timeseries(org):
    """
    Rollup org timeseries => org summary.
    """
    pass


def summary_select(metrics_to_select):
    """
    generate aggregation statments + list of metric names.
    """
    summary_pattern = "{agg}({name}) AS {name}"
    select_statements = []
    metrics = []
    for n, m in metrics_to_select.items():
        ss = summary_pattern.format(**m)
        select_statements.append(ss)
        metrics.append(n)
    return ", ".join(metrics), ",\n".join(select_statements)


def computed_query(query, computed_metrics):
    """
    Add computed metrics to a query.
    """
    selects = []
    for n, m in computed_metrics.items():
        formula = m.get('formula')
        formula = formula.replace('{', '"').replace('}', '"')
        selects.append("{f} as {name}".format(f=formula, **m))
    if len(selects):
        selects = "," + "\n\t,".join(selects)
    else:
        selects = ""
    return \
        """SELECT base_query.*
              {0}
        FROM (
            {1}
        )
        AS base_query
    """.format(selects, query)

if __name__ == '__main__':
    from newslynx.models import Org 
    o = Org.query.get(1)
    print org_timeseries_from_content_timeseries(o)
