from newslynx.core import db
from newslynx.lib import dates
from newslynx.exc import RequestError
from newslynx.tasks import ingest_util
from newslynx.lib.serialize import obj_to_json


def content_timeseries(
        obj,
        org_id=None,
        metrics_lookup=None,
        content_item_ids=None,
        commit=True):
    """
    Ingest Timeseries Metrics for a content item.
    """
    # if not content_item_id or not org or not metrics_lookup:
    #     raise RequestError('Missing required kwargs.')
    content_item_id = obj.pop('content_item_id')
    if not content_item_id:
        raise RequestError('Object is missing a "content_item_id"')
    if not content_item_id in content_item_ids:
        raise RequestError(
            'Content Item with ID {} doesnt exist'.format(content_item_id))

    cmd_kwargs = {
        "org_id": org_id,
        "content_item_id": content_item_id
    }

    # parse datetime.
    if 'datetime' not in obj:
        cmd_kwargs['datetime'] = dates.floor_now(
            unit='hour', value=1).isoformat()

    else:
        ds = obj.pop('datetime')
        dt = dates.parse_iso(ds)
        cmd_kwargs['datetime'] = dates.floor(
            dt, unit='hour', value=1).isoformat()

    metrics = ingest_util.prepare_metrics(
        obj,
        metrics_lookup,
        valid_levels=['content_item', 'all'],
        check_timeseries=True)

    # upsert command
    cmd = """SELECT upsert_content_metric_timeseries(
                {org_id},
                {content_item_id},
                '{datetime}',
                '{metrics}')
           """.format(metrics=obj_to_json(metrics), **cmd_kwargs)

    if commit:
        try:
            db.session.execute(cmd)
        except Exception as err:
            raise RequestError(err.message)
        cmd_kwargs['metrics'] = metrics
    return cmd


def content_summary(
        obj,
        org_id=None,
        metrics_lookup=None,
        content_item_ids=None,
        commit=True):
    """
    Ingest Summary Metrics for a content item.
    """
    content_item_id = obj.pop('content_item_id')
    if not content_item_id:
        raise RequestError('Object is missing a "content_item_id"')
    if not content_item_id in content_item_ids:
        raise RequestError(
            'Content Item with ID {} doesnt exist'.format(content_item_id))

    cmd_kwargs = {
        "org_id": org_id,
        "content_item_id": content_item_id
    }

    metrics = ingest_util.prepare_metrics(
        obj,
        metrics_lookup,
        valid_levels=['content_item', 'all'],
        check_timeseries=False)

    # upsert command
    cmd = """SELECT upsert_content_metric_summary(
                {org_id},
                {content_item_id},
                '{metrics}')
           """.format(metrics=obj_to_json(metrics), **cmd_kwargs)

    if commit:
        try:
            db.session.execute(cmd)
        except Exception as err:
            raise RequestError(err.message)
        cmd_kwargs['metrics'] = metrics
    return cmd


def org_timeseries(
        obj,
        org_id=None,
        metrics_lookup=None,
        commit=True):
    """
    Ingest Timeseries Metrics for an organization.
    """
    cmd_kwargs = {
        'org_id': org_id
    }

    # parse datetime.
    if 'datetime' not in obj:
        cmd_kwargs['datetime'] = dates.floor_now(
            unit='hour', value=1).isoformat()

    else:
        ds = obj.pop('datetime')
        dt = dates.parse_iso(ds)
        cmd_kwargs['datetime'] = dates.floor(
            dt, unit='hour', value=1).isoformat()

    metrics = ingest_util.prepare_metrics(
        obj,
        metrics_lookup,
        valid_levels=['org', 'all'],
        check_timeseries=True)

    # upsert command
    cmd = """SELECT upsert_org_metric_timeseries(
                 {org_id},
                '{datetime}',
                '{metrics}')
           """.format(metrics=obj_to_json(metrics), **cmd_kwargs)

    if commit:
        try:
            db.session.execute(cmd)
        except Exception as err:
            raise RequestError(err.message)
        cmd_kwargs['metrics'] = metrics
        return cmd_kwargs
    return cmd


def org_summary(
        obj,
        org_id,
        metrics_lookup,
        commit=True):
    """
    Ingest Summary Metrics for an organization.
    """
    cmd_kwargs = {
        "org_id": org_id
    }

    metrics = ingest_util.prepare_metrics(
        obj,
        metrics_lookup,
        valid_levels=['org', 'all'],
        check_timeseries=False)

    # upsert command
    cmd = """SELECT upsert_org_metric_summary(
                 {org_id},
                '{metrics}')
           """.format(metrics=obj_to_json(metrics), **cmd_kwargs)

    if commit:
        try:
            db.session.execute(cmd)
        except Exception as err:
            raise RequestError(err.message)
        cmd_kwargs['metrics'] = metrics
    return cmd
