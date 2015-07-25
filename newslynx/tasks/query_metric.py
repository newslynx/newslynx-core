"""
Query Logic for timeseries datastores.
"""

from datetime import datetime, date
import copy

from newslynx.core import db
from newslynx.tasks.util import ResultIter
from newslynx.util import uniq



class TSQuery(object):

    """
    An abstract model for querying our timeseries stores.
    """
    table = None
    id_col = None
    metrics_attr = None
    computed_metrics_attr = None
    cal_fx = None

    date_col = 'datetime'
    metrics_col = 'metrics'
    init_table = 'init'
    sparse_table = 'sparse'
    min_unit = 'hour'

    def __init__(self, org, ids, **kw):
        self.org = org
        if not isinstance(ids, list):
            ids = [ids]
        self.ids = ids
        self.select = kw.get('select', '*') # TODO
        self.exclude = kw.get('exclude', []) # TODO
        self.unit = kw.get('unit', self.min_unit)
        self.sparse = kw.get('sparse', True)
        self.sig_digits = kw.get('sig_digits', 2)
        self.group_by_id = kw.get('group_by_id', True)
        self.rm_nulls = kw.get('rm_nulls', False)
        self.time_since_start = kw.get('time_since_start', False)  # TODO
        # cumulative, avg, median, per_change, roll_avg
        self.transform = kw.get('transform', None)
        self.before = kw.get('before', None)
        self.after = kw.get('after', None)
        self.metrics = getattr(org, self.metrics_attr)
        self.computed_metrics = getattr(org, self.computed_metrics_attr)
        # self.select_metrics()
        self.format_dates()
        self.compute = len(self.computed_metrics.keys()) > 0

    # @property
    # def computed_metrics_require(self):
    #     """
    #     Which metrics to do computed metrics require?
    #     """
    #     required = []
    #     for metric in self.computed_metrics.values():
    #         if self.select == "*":

    #             required.extend(metric.get('formula_requires', []))

    #         elif metric['name'] in self.select and \
    #                 not metric['name'] in self.exclude:

    #             required.extend(metric.get('formula_requires', []))

    #     return uniq(required)

    # # TODO : Figure out how to deal with metrics which
    # # computed metrics are reliant upon.
    # def select_metrics(self):
    #     """
    #     Select / exclude computed metrics.
    #     """
    #     select = copy.copy(self.select)

    #     if select != "*":
    #         if not isinstance(select, list):
    #             select = [select]

    #         for n in self.metrics.keys():
    #             if n not in select and n not in self.computed_metrics_require:
    #                 self.metrics.pop(n)

    #         for n in self.computed_metrics.keys():
    #             if n not in self.select:
    #                 self.computed_metrics.pop(n)

    #     exclude = copy.copy(self.exclude)
    #     if not isinstance(exclude, list):
    #         exclude = [exclude]

    #     if len(exclude):
    #         for n in self.metrics.keys():
    #             if n in self.exclude:
    #                 self.metrics.pop(n)

    #         for n in self.computed_metrics.keys():
    #             if n in self.exclude:
    #                 self.computed_metrics.pop(n)

    def format_dates(self):
        """
        Format dates.
        """
        self.filter_dates = False
        if self.before:
            self.filter_dates = True
            self.before = self.format_date(self.before)

        if self.after:
            self.filter_dates = True
            self.after = self.format_date(self.after)

    def format_date(self, d):
        """
        Format a date
        """
        if isinstance(d, (datetime, date)):
            return d.isoformat()
        return d

    @property
    def ids_array(self):
        """
        The array of ids to select.
        """
        idstring = ", ".join([str(i) for i in self.ids])
        return "ARRAY[{}]".format(idstring)

    @property
    def date_filter(self):
        """
        Filter by date.
        """
        clauses = []
        fmt = "{} {} '{}'"
        if not self.filter_dates:
            return ""

        if self.before:
            c = fmt.format(self.date_col, "<=", self.before)
            clauses.append(c)

        if self.after:
            c = fmt.format(self.date_col, ">=", self.after)
            clauses.append(c)

        return "AND {}".format(" AND ".join(clauses))

    @property
    def query_kw(self):
        """
        default kwargs.
        """
        return dict(
            table=self.table,
            id_col=self.id_col,
            date_col=self.date_col,
            sig_digits=self.sig_digits,
            metrics_col=self.metrics_col,
            unit=self.unit,
            cal_fx=self.cal_fx,
            sparse_table=self.sparse_table,
            ids_array=self.ids_array,
            date_filter=self.date_filter
        )

    def add_kw(self, **kw):
        """
        Update default kw.
        """
        return dict(self.query_kw.items() + kw.items())

    # SELECT STATEMENTS

    def select_json(self, metric):
        """
        Pull a json key out of the metrics store.
        """
        return "({metrics_col} ->> '{name}')::text::numeric"\
               .format(**self.add_kw(**metric))

    def select_simple(self, metric):
        """
        A simple select statement for the initial, sparse query.
        """
        j = self.select_json(metric)
        return "{j} as {name}".format(j=j, **self.add_kw(**metric))

    def select_compute(self, metric):
        """
        compute a metrics. we're assuming formula is validating at this point.
        """
        formula = metric.get('formula')
        formula = formula.replace('{', '"').replace('}', '"')
        return "{f} as {name}".format(f=formula, **metric)

    def select_cumulative_to_count(self, metric):
        """
        Generate a select statement for a cumulative metric to turn it into a count.
        """
        j = self.select_json(metric)
        return """COALESCE(
                    {j} - lag({j}) OVER (PARTITION BY {id_col} ORDER BY {date_col} ASC),
                    {j}) as {name}""".format(j=j, **self.add_kw(**metric))

    def select_agg(self, metric):
        """
        A select statement for the agg query.
        """
        s = "ROUND({agg}({name}), {sig_digits}) as {name}"
        return s.format(**self.add_kw(**metric))

    def select_non_sparse(self, metric):
        """
        A non-sparse select statement.
        """
        s = "COALESCE({sparse_table}.{name}, 0) as {name}"
        return s.format(**self.add_kw(**metric))

    def select_cumulative(self, metric):
        """
        A select statement to make a count metric cumulative.
        """
        p = "PARTITION BY {}".format(self.id_col)
        if not self.group_by_id:
            p = ""
        s = "sum({name}) OVER ({p} ORDER BY {date_col} ASC) AS {name}"
        return s.format(p=p, **self.add_kw(**metric))

    @property
    def init_selects(self):
        """
        Generate select statements for the initial query.
        """
        ss = []
        for n, m in self.metrics.items():
            if m['type'] == 'cumulative':
                ss.append(self.select_cumulative_to_count(m))
            else:
                ss.append(self.select_simple(m))
        return ",\n".join(ss)

    @property
    def agg_selects(self):
        """
        Generate select statements for the aggregation query.
        """
        ss = []
        for n, m in self.metrics.items():
            ss.append(self.select_agg(m))
        return ",\n".join(ss)

    @property
    def compute_selects(self):
        """
        Generate select statements for the calculation query.
        """
        ss = []
        for n, m in self.computed_metrics.items():
            ss.append(self.select_compute(m))
        # passthrough other metrics
        for n, m in self.metrics.items():
            ss.append(n)
        return ",\n".join(ss)

    @property
    def non_sparse_selects(self):
        """
        Generate select statements for the non sparse query.
        """
        ss = []
        for n, m in self.metrics.items():
            ss.append(self.select_non_sparse(m))
        return ",\n".join(ss)

    @property
    def cumulative_selects(self):
        """
        Generate select statements for the cumulative query.
        """
        ss = []
        for n, m in dict(self.metrics.items() + self.computed_metrics.items()).items():
            if m['agg'] == 'sum':
                ss.append(self.select_cumulative(m))
            else:
                ss.append(n)
        return ",\n".join(ss)

    @property
    def init_kw(self):
        """
        kwargs for the initial query.
        """
        init_id_col = "{},".format(self.id_col)
        if not self.group_by_id:
            init_id_col = ""

        # optionally ignore date
        date_select = "date_trunc('{unit}', {date_col}) as {date_col},"\
            .format(**self.query_kw)
        if self.unit is None:
            date_select = ""

        return self.add_kw(
            select=self.init_selects,
            init_id_col=init_id_col,
            date_select=date_select
        )

    @property
    def init_query(self):
        """
        The initial query.
        """
        return \
            """SELECT
                    {init_id_col}
                    {date_select}
                    {select}
                FROM {table}
                    WHERE {id_col} IN (select unnest({ids_array}))
                    {date_filter}
            """.format(**self.init_kw)

    @property
    def agg_kw(self):
        """
        kwargs for the aggregation query.
        """
        # group by ID ?
        agg_id_col = "{0},".format(self.id_col)
        sel_id_col = copy.copy(agg_id_col)
        agg_order_by = ",{0}".format(self.id_col)

        # if we're ignoring the date, we need to get
        # change these commas
        if not self.unit:
            agg_id_col = agg_id_col.replace(',', '')
            agg_order_by = agg_order_by.replace(',', '')

        if not self.group_by_id:
            agg_id_col = ""
            sel_id_col = ""
            agg_order_by = ""

        # optionally ignore date
        date_select = "date_trunc('{unit}', {date_col}) as {date_col},"\
                      .format(**self.query_kw)
        date_col = copy.copy(self.date_col)
        if self.unit is None:
            date_select = ""
            date_col = ""

        # add order by + group by
        order_by = "ORDER BY {} {} ASC".format(date_col, agg_order_by)
        if not date_col and not agg_order_by:
            order_by = ""

        group_by = "GROUP BY {} {}".format(agg_id_col, date_col)
        if not date_col and not agg_id_col:
            group_by = ""

        # format kwargs
        return self.add_kw(
            select=self.agg_selects,
            date_select=date_select,
            init_query=self.init_query,
            agg_id_col=agg_id_col,
            sel_id_col=sel_id_col,
            agg_order_by=agg_order_by,
            date_col=date_col,
            group_by=group_by,
            order_by=order_by
        )

    @property
    def agg_query(self):
        """
        The aggregation query.
        """
        return \
            """SELECT {sel_id_col}
                    {date_select}
                    {select}
                FROM ({init_query}) t1
                {group_by}
                {order_by}
            """.format(**self.agg_kw)

    @property
    def cal_kw(self):
        """
        kwargs for non-sparse calendar
        """
        before = ""
        after = ""
        if self.before:
            before = ", '{}'".format(self.before)
        if self.after:
            after = ", '{}'".format(self.after)
        return self.add_kw(before=before, after=after)

    @property
    def cal(self):
        """
        The calendar for the non-sparse query.
        """
        p = "{cal_fx}('1 {unit}s', {ids_array} {after} {before})"
        return p.format(**self.cal_kw)

    @property
    def non_sparse_kw(self):
        """
        kwargs for the non-sparse query.
        """
        if self.unit == self.min_unit:
            init_q = self.init_query
        else:
            init_q = self.agg_query

        if self.compute:
            init_q = self.computed_query(init_q)

        # group by ID ?
        cal_id_col1 = "{0},\n".format(self.id_col)
        cal_id_col2 = "cal.{0}".format(cal_id_col1)
        cal_id_join = "AND cal.{0} = {1}.{0}"\
                      .format(self.id_col, self.sparse_table)
        cal_order_by = ", cal.{0}".format(self.id_col)
        cal_date_select = "{}".format(self.date_col)

        if not self.group_by_id:
            cal_id_col1 = ""
            cal_id_col2 = ""
            cal_id_join = ""
            cal_order_by = ""
            cal_date_select = "distinct({})".format(self.date_col)

        return self.add_kw(
            select=self.non_sparse_selects,
            init_q=init_q,
            cal=self.cal,
            cal_id_join=cal_id_join,
            cal_id_col1=cal_id_col1,
            cal_id_col2=cal_id_col2,
            cal_order_by=cal_order_by,
            cal_date_select=cal_date_select
        )

    @property
    def non_sparse_query(self):
        """
        The non-sparse query.
        """
        return \
            """WITH {sparse_table} as (
                    {init_q}
                ),
                cal as (
                    select
                        {cal_id_col1}
                        {cal_date_select}
                        from {cal}
                )
                SELECT
                       {cal_id_col2}
                       cal.{date_col},
                       {select}
                FROM cal
                LEFT JOIN {sparse_table} ON
                    cal.{date_col} = {sparse_table}.{date_col}
                    {cal_id_join}
                ORDER BY cal.{date_col} {cal_order_by} ASC
            """.format(**self.non_sparse_kw)

    def computed_query(self, init_q):
        """
        A computed query is special in that
        it must come after selects
        + aggregations queries but before
        transformations.
        """
        kw = {
            "init_q": init_q,
            "select": self.compute_selects,
            'com_id_col': "{},".format(self.id_col)
        }
        if not self.group_by_id:
            kw['com_id_col'] = ""

        if self.unit is None:
            kw['date_col'] = ""
        else:
            kw['date_col'] = copy.copy(self.date_col) + ","
        return \
            """SELECT
                {com_id_col}
                {date_col}
                {select}
               FROM ({init_q}) tttt
            """.format(**self.add_kw(**kw))

    @property
    def cumulative_kw(self):
        """
        kwargs for the cumulative query.
        """
        # determine initial query
        if self.sparse and self.unit == 'hour' and self.group_by_id:
            init_q = self.init_query

        elif self.sparse:
            init_q = self.agg_query

        elif not self.sparse:
            init_q = self.non_sparse_query

        _id_col = "{},".format(self.id_col)
        if not self.group_by_id:
            _id_col = ""

        if self.compute:
            init_q = self.computed_query(init_q)

        return self.add_kw(
            select=self.cumulative_selects,
            init_q=init_q,
            _id_col=_id_col
        )

    @property
    def cumulative_query(self):
        """
        The cumulative query.
        """
        return \
            """ SELECT
                    {date_col},
                    {_id_col}
                    {select}
                FROM (
                    {init_q}
                ) t2
            """.format(**self.cumulative_kw)

    @property
    def query(self):
        """
        The whole shebang
        """

        # simple query.
        if self.sparse and \
           self.unit == self.min_unit and \
           not self.transform:

            if not self.compute:
                return self.init_query
            return self.computed_query(self.init_query)

        # aggregate by content id query
        elif self.unit is None:
            if not self.compute:
                return self.agg_query
            return self.computed_query(self.agg_query)

        # simple aggregate query
        elif self.sparse and not self.transform:

            if not self.compute:
                return self.agg_query
            return self.computed_query(self.agg_query)

        # non-sparse query
        elif not self.sparse and not self.transform:
            if not self.compute:
                return self.non_sparse_query
            return self.computed_query(self.non_sparse_query)

        # cumulative
        elif self.transform == 'cumulative':
            return self.cumulative_query

        # TODO: rolling average, per_change, median + average timeseries for
        # multiple ids.

        # return self.cumulative_query

    def select_metrics(self, results):
        """
        Filter out only the metrics that matter.
        """
        # rudimentary select for now.
        for row in results:
            clean_row = {}
            if len(self.exclude):
                for k in self.exclude:
                    row.pop(k, None)
            if len(self.select) and self.select != "*":
                for k in self.select:
                    clean_row[k] = row.pop(k)
            yield clean_row

    def execute(self):
        """
        Execute the query and stream the results.
        """
        return ResultIter(db.session.execute(self.query))
        # return self.select_metrics(res)


class QueryContentMetricTimeseries(TSQuery):
    table = "content_metric_timeseries"
    id_col = "content_item_id"
    cal_fx = "content_metric_calendar"
    metrics_attr = "content_timeseries_metrics"
    computed_metrics_attr = "computed_content_timeseries_metrics"


class QueryOrgMetricTimeseries(TSQuery):
    table = "org_metric_timeseries"
    id_col = "org_id"
    cal_fx = "org_metric_calendar"
    metrics_attr = "timeseries_metrics"
    computed_metrics_attr = "computed_timeseries_metrics"
