from newslynx.core import db
from newslynx.lib import dates
from newslynx.exc import RequestError
from newslynx.tasks import ingest_util
from newslynx.lib.serialize import obj_to_json


def ingest_content_metric_timeseries(
        obj,
        content_item_id,
        org_id,
        org_metric_lookup,
        commit=True):
    """
    Ingest Timeseries Metrics for a content item.
    """
    cmd_kwargs = {
        'org_id': org_id,
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
        org_metric_lookup,
        valid_levels=['content_item', 'all'],
        check_timeseries=True)

    # upsert command
    cmd = """SELECT upsert_content_metric_timeseries(
                {org_id},
                {content_item_id},
                '{datetime}',
                '{metrics}');
           """.format(metrics=obj_to_json(metrics), **cmd_kwargs)
    try:
        db.session.execute(cmd)
    except Exception as err:
        raise RequestError(err.message)
    cmd_kwargs['metrics'] = metrics
    return cmd_kwargs


def ingest_content_metric_summary(
        obj,
        content_item_id,
        org_id,
        org_metric_lookup,
        commit=True):
    """
    Ingest Summary Metrics for a content item.
    """
    cmd_kwargs = {
        "org_id": org_id,
        "content_item_id": content_item_id
    }

    metrics = ingest_util.prepare_metrics(
        obj,
        org_metric_lookup,
        valid_levels=['content_item', 'all'],
        check_timeseries=False)

    # upsert command
    cmd = """SELECT upsert_content_metric_summary(
                {org_id},
                {content_item_id},
                '{metrics}');
           """.format(metrics=obj_to_json(metrics), **cmd_kwargs)
    try:
        db.session.execute(cmd)
    except Exception as err:
        raise RequestError(err.message)
    cmd_kwargs['metrics'] = metrics
    return cmd_kwargs


def ingest_org_metric_timeseries(
        obj,
        org_id,
        org_metric_lookup,
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
        org_metric_lookup,
        valid_levels=['org', 'all'],
        check_timeseries=True)

    # upsert command
    cmd = """SELECT upsert_org_metric_timeseries(
                 {org_id},
                '{datetime}',
                '{metrics}');
           """.format(metrics=obj_to_json(metrics), **cmd_kwargs)
    try:
        db.session.execute(cmd)
    except Exception as err:
        raise RequestError(err.message)
    cmd_kwargs['metrics'] = metrics
    return cmd_kwargs


def ingest_org_metric_summary(
        obj,
        org_id,
        org_metric_lookup,
        commit=True):
    """
    Ingest Summary Metrics for an organization.
    """
    cmd_kwargs = {
        "org_id": org_id
    }

    metrics = ingest_util.prepare_metrics(
        obj,
        org_metric_lookup,
        valid_levels=['org', 'all'],
        check_timeseries=False)

    # upsert command
    cmd = """SELECT upsert_org_metric_summary(
                 {org_id},
                '{metrics}');
           """.format(metrics=obj_to_json(metrics), **cmd_kwargs)
    try:
        db.session.execute(cmd)
    except Exception as err:
        raise RequestError(err.message)
    cmd_kwargs['metrics'] = metrics
    return cmd_kwargs
