"""
All utilities related to dates, times, and timezones.
"""
from datetime import datetime

import pytz
import iso8601


def now(ts=False):
    """
    Get the current datetime / timestamp
    """
    dt = datetime.utcnow()
    dt = dt.replace(tzinfo=pytz.utc)
    if ts:
        return int(dt.strftime('%s'))
    return dt


def ts(ts):
    """
    Get a datetime object from a timestamp.
    """
    dt = datetime.utcfromtimestamp(ts)
    dt = dt.replace(tzinfo=pytz.utc)
    return dt


def parse_iso(ds, default_tz=pytz.utc):
    """
    parse an isodate/datetime string with or without
    a datestring.
    """

    try:
        dt = iso8601.parse_date(ds)
    except:
        return None

    tz = getattr(dt, 'tzinfo', None)
    if tz:
        if tz:
            return datetime(
                year=dt.year,
                month=dt.month,
                day=dt.day,
                hour=getattr(dt, 'hour', 0),
                minute=getattr(dt, 'minute',  0,),
                second=getattr(dt, 'second', 0),
                tzinfo=tz
            )

    return datetime(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=getattr(dt, 'hour', 0),
        minute=getattr(dt, 'minute',  0,),
        second=getattr(dt, 'second', 0),
        tzinfo=default_tz
    )
