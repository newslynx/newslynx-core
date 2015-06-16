from newslynx.core import db


def content_ts(org, content_item_id, **kw):
    """
    Fetch a timeseries for a content_item
    """

    # get the org's content timeseries metrics
    metrics = org.content_timeseries_metrics()

    sparse = kw.get('sparse', True)
    unit = kw.get('unit', 'hour')
    cumulative = kw.get('cumulative', False)

    cols = ['content_item_id', 'datetime']

    # fetch metrics
    sparse_statements, metric_columns = \
        _gen_sparse_select_statements(metrics)

    # add metric columns
    cols += metric_columns

    # format kwargs for query
    qkw = {
        'content_item_id': content_item_id,
        'unit': unit,
        'select_statements': ",\n".join(sparse_statements)
    }

    # generate sparse query
    query = """
        SELECT content_item_id,
            date_trunc('{unit}', datetime) as datetime,
            {select_statements}
        FROM content_metric_timeseries
        WHERE content_item_id = {content_item_id}
        GROUP BY content_item_id, date_trunc('{unit}', datetime)
        ORDER BY datetime ASC
        """.format(**qkw)

    # if the timeseries should be filled in, update the query.
    if not sparse:

        non_sparse_statements = _gen_non_sparse_select_statements(metrics)
        qkw['select_statements'] = ",\n".join(non_sparse_statements)
        qkw['init_q'] = query

        query = """
            with stats as (
                {init_q}
            ),
            cal as (
                select * from content_metric_calendar('1 {unit}s', {content_item_id})
            )
            SELECT cal.content_item_id,
                   cal.datetime,
                   {select_statements}
            FROM cal
            LEFT JOIN stats ON
                cal.datetime = stats.datetime AND
                cal.content_item_id = stats.content_item_id
            GROUP BY cal.content_item_id, cal.datetime
            ORDER BY cal.datetime ASC
        """.format(**qkw)

    # if the query should return cumulative counts, reformat the query again.
    if cumulative:

        cumulative_statements = _gen_cumulative_select_statements(metrics)
        qkw['select_statements'] = ",\n".join(cumulative_statements)
        qkw['init_q'] = query

        query = """
        SELECT content_item_id, datetime,
            {select_statements}
        FROM (
            {init_q}
        ) t
        """.format(**qkw)

    # execute the query and format the results as a dictionary
    output = []
    for row in db.session.execute(query):
        output.append(dict(zip(cols, row)))
    return output


def org_ts(org, **kw):
    """
    Fetch a timeseries for an org
    """

    # get the org's content timeseries metrics
    metrics = org.timeseries_metrics()

    sparse = kw.get('sparse', True)
    unit = kw.get('unit', 'hour')
    cumulative = kw.get('cumulative', False)

    cols = ['org_id', 'datetime']

    # fetch metrics
    sparse_statements, metric_columns = \
        _gen_sparse_select_statements(metrics)

    # add metric columns
    cols += metric_columns

    # format kwargs for query
    qkw = {
        'org_id': org.id,
        'unit': unit,
        'select_statements': ",\n".join(sparse_statements)
    }

    # generate sparse query
    query = """
        SELECT org_id,
            date_trunc('{unit}', datetime) as datetime,
            {select_statements}
        FROM org_metric_timeseries
        WHERE org_id = {org_id}
        GROUP BY org_id, date_trunc('{unit}', datetime)
        ORDER BY datetime ASC
        """.format(**qkw)

    # if the timeseries should be filled in, update the query.
    if not sparse:

        non_sparse_statements = _gen_non_sparse_select_statements(metrics)
        qkw['select_statements'] = ",\n".join(non_sparse_statements)
        qkw['init_q'] = query

        query = """
            with stats as (
                {init_q}
            ),
            cal as (
                select * from org_metric_calendar('1 {unit}s', {org_id})
            )
            SELECT cal.org_id,
                   cal.datetime,
                   {select_statements}
            FROM cal
            LEFT JOIN stats ON
                cal.datetime = stats.datetime AND
                cal.org_id = stats.org_id
            GROUP BY cal.org_id, cal.datetime
            ORDER BY cal.datetime ASC
        """.format(**qkw)

    # if the query should return cumulative counts, reformat the query again.
    if cumulative:

        cumulative_statements = _gen_cumulative_select_statements(metrics, id_col='org_id')
        qkw['select_statements'] = ",\n".join(cumulative_statements)
        qkw['init_q'] = query

        query = """
        SELECT org_id, datetime,
            {select_statements}
        FROM (
            {init_q}
        ) t
        """.format(**qkw)

    # execute the query and format the results as a dictionary
    output = []
    for row in db.session.execute(query):
        output.append(dict(zip(cols, row)))
    return output


def _gen_sparse_select_statements(metrics):
    """
    Generate select statements for a list of metrics
    """
    select_pattern = """
        ROUND({aggregation}(COALESCE((metrics ->> '{name}')::text::numeric, 0)), 2) as {name}
    """

    statements = []
    columns = []
    for m in metrics:
        statements.append(select_pattern.format(**m.to_dict()))
        columns.append(m.name)
    return statements, columns


def _gen_non_sparse_select_statements(metrics, table='stats'):
    """
    Generate select statements for a list of metrics
    """
    select_pattern = """
        ROUND({aggregation}(COALESCE({table}.{name}, 0)), 2) as {name}
    """

    statements = []
    for m in metrics:
        kw = m.to_dict()
        kw['table'] = table
        statements.append(select_pattern.format(**kw))
    return statements


def _gen_cumulative_select_statements(metrics, id_col='content_item_id'):
    """
    Generate select statements for a list of metrics
    """
    select_pattern = """
        sum({name}) OVER (PARTITION BY {id_col} ORDER BY datetime ASC) AS {name}
    """

    statements = []
    for m in metrics:
        if m.aggregation != 'sum':
            statements.append(m.name)
        else:
            kw = m.to_dict()
            kw['id_col'] = id_col
            statements.append(select_pattern.format(**kw))
    return statements
