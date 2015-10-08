from newslynx.core import db


def refresh_all(org):
    """
    Shortcut.
    """
    content_summary(org)
    org_summary(org)
    return True


def content_summary(org):
    """
    Content summary computed metrics.
    """
    return computed_query(
        org,
        'content_metric_summary',
        org.computed_content_summary_metrics,
        org.computable_content_summary_metrics,
        extra_cols=['org_id', 'content_item_id']
    )


def org_summary(org):
    """
    Org summary computed metrics
    """
    return computed_query(
        org,
        'org_metric_summary',
        org.computed_summary_metrics,
        org.computable_summary_metrics,
        extra_cols=['org_id']
    )


def computed_query(org, table, computed_metrics, source_metrics, extra_cols=[]):
    """
    Compute metrics and store them back.
    """
    computes = []
    metrics = []
    for n, m in computed_metrics.items():
        formula = m.get('formula')
        formula = formula.replace('{', '"').replace('}', '"')
        computes.append("{f} as {name}".format(f=formula, **m))
        metrics.append(n)

    if len(computes):
        computes = "\n\t,".join(computes)
        metrics = ",".join(metrics)

    # no need to continue
    else:
        return True

    # grab sources
    sources = _json_select(source_metrics)

    # no need to continue
    if not len(sources):
        return True

    # query kwargs
    qkw = {
        'table': table,
        'extra_cols': ",".join(extra_cols),
        'metrics': metrics,
        'computes': computes,
        'sources': sources,
        'org_id': org.id
    }

    q = \
        """SELECT upsert_{table}({extra_cols}, metrics::text)
           FROM  (
              SELECT
                {extra_cols},
                (SELECT row_to_json(_) from (SELECT {metrics}) as _) as metrics
              FROM (
                SELECT
                    {extra_cols},
                    {computes}
                FROM (
                  SELECT
                    {extra_cols},
                    {sources}
                  FROM {table}
                  WHERE org_id = {org_id}
                ) t1
              ) t2
           ) t3
    """.format(**qkw)
    db.session.execute(q)
    db.session.commit()
    return True


def _json_select(metrics_to_select):
    """
    Pull a json key out of the metrics column.
    """
    s = "(metrics ->> '{name}')::text::numeric as {name}"
    select_statements = []
    for n, m in metrics_to_select.items():
        ss = s.format(**m)
        select_statements.append(ss)
    return ",\n".join(select_statements)

if __name__ == '__main__':
    from newslynx.models import Org
    org = Org.query.get(1)
    org_summary(org)
