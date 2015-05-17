from sqlalchemy import func, desc, asc

from newslynx.models import Metric
from newslynx.core import db_session
from newslynx.constants import (
    THING_TIMESERIES_MAT_VIEW,
    ORG_TIMESERIES_MAT_VIEW)


def create_mat_view(name, sql):
    """
    Create/replace a materialized view.
    """
    q = """
        CREATE EXTENSION IF NOT EXISTS tablefunc;
        DROP MATERIALIZED VIEW IF EXISTS {0};
        CREATE MATERIALIZED VIEW {0} AS\n{1}
        """.format(name, sql)
    db_session.execute(q)
    db_session.commit()


def thing_timeseries():
    """
    Take the long metrics table and crosstab
    it into a filled-in timeseries.
    """

    # fetch all timeseries metrics.
    metrics = db_session.query(func.distinct(Metric.name))\
        .filter(Metric.thing_id != None)\
        .filter(Metric.created != None)\
        .filter_by(level='thing')\
        .order_by(Metric.name.asc())\
        .all()
    metric_names = [m[0] for m in metrics]

    # formulate coalese statements + schema stmnts
    coalesce_stmnts = []
    cstmnt = "SUM(coalesce({0}, 0)) AS {0}"

    schema_stmnts = []
    sstmnt = "{} numeric"
    for name in metric_names:

        coalesce_stmnts.append(cstmnt.format(name))
        schema_stmnts.append(sstmnt.format(name))

    # query args
    query_args = {
        'coalesce': ",\n".join(coalesce_stmnts),
        'schema': ",\n".join(schema_stmnts)
    }

    sql =\
        """ WITH stats as (
            SELECT
                thing_id, datetime,
                {coalesce}
            from crosstab(
                'SELECT
                    thing_id, date_trunc_by_hours(1, created) AS datetime, name, SUM(value) AS value
                 FROM metrics
                 WHERE created IS NOT NULL AND level = ''thing''
                 GROUP BY datetime, name, thing_id
                 ORDER BY datetime, name ASC',
                'SELECT
                    distinct(name)
                 FROM metrics
                 WHERE created IS NOT NULL
                 AND level = ''thing''
                 ORDER BY name ASC'
            ) as
                ct(
                    thing_id int,
                    datetime timestamp with time zone,
                    {schema}
                )
            GROUP BY thing_id, datetime
            ORDER BY datetime, thing_id ASC
        ),

        calendar AS (
            select datetime, thing_id, org_id from thing_metrics_calendar('1 hour')
        )

        SELECT calendar.org_id,
               calendar.thing_id,
               calendar.datetime,
               {coalesce}
        FROM calendar
        LEFT JOIN stats ON calendar.datetime = stats.datetime AND calendar.thing_id = stats.thing_id
        GROUP BY calendar.org_id, calendar.thing_id, calendar.datetime
        ORDER BY calendar.datetime, calendar.thing_id ASC
    """.format(**query_args)
    return create_mat_view(THING_TIMESERIES_MAT_VIEW, sql)


def org_timeseries():
    """
    Take the long metrics table and crosstab
    it into a filled-in timeseries.
    """

    # fetch all timeseries metrics.
    metrics = db_session.query(func.distinct(Metric.name))\
        .filter(Metric.created != None)\
        .filter_by(level='org')\
        .all()
    metric_names = [m[0] for m in metrics]

    # formulate coalese statements + schema stmnts
    coalesce_stmnts = []
    cstmnt = "SUM(coalesce({0}, 0)) AS {0}"

    schema_stmnts = []
    sstmnt = "{} numeric"
    for name in metric_names:

        coalesce_stmnts.append(cstmnt.format(name))
        schema_stmnts.append(sstmnt.format(name))

    # query args
    query_args = {
        'coalesce': ",\n".join(coalesce_stmnts),
        'schema': ",\n".join(schema_stmnts)
    }

    sql =\
        """ WITH stats as (
            SELECT
                datetime,
                org_id,
                {coalesce}
            from crosstab(
                'SELECT
                    date_trunc_by_hours(1, created)::text || org_id::text as temp_id,
                    date_trunc_by_hours(1, created) AS datetime,
                    org_id,
                    name,
                    SUM(value) AS value
                 FROM metrics
                 WHERE created IS NOT NULL AND level = ''org''
                 GROUP BY datetime, name, org_id
                 ORDER BY datetime, name ASC',
                'SELECT
                 distinct(name)
                 FROM metrics
                 WHERE created IS NOT NULL
                 AND level = ''org''
                 ORDER BY name ASC'
            ) as
                ct(
                    temp_id text,
                    datetime timestamp with time zone,
                    org_id int,
                    {schema}
                )
            GROUP BY org_id, datetime
            ORDER BY datetime, org_id ASC
        ),

        calendar AS (
            select datetime, org_id from org_metrics_calendar('1 hour')
        )

        SELECT calendar.org_id,
               calendar.datetime,
               {coalesce}
        FROM calendar
        LEFT JOIN stats ON calendar.datetime = stats.datetime AND calendar.org_id = stats.org_id
        GROUP BY calendar.org_id, calendar.datetime
        ORDER BY calendar.datetime, calendar.org_id ASC
    """.format(**query_args)
    return create_mat_view(ORG_TIMESERIES_MAT_VIEW, sql)
