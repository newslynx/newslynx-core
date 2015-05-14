"""
All utilities related to dates, times, and timezones.
"""
from datetime import datetime, time
import re

import pytz
import iso8601

# a regex for parsing time of day (IE 12:00 AM, 12:00PM)
# to a datetime.time object
re_time = re.compile(r'([0-9]{1,2}):([0-9]{1,2}) (AM|PM)')


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
    a datestring. Return None if there's an error.
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


def parse_time_of_day(string):
    """
    12:00 AM > datetime.time
    12:00 PM > datetime.time
    """
    m = re_time.search(string)
    hour = int(m.group(1))
    minute = int(m.group(2))
    am_pm = m.group(3)

    # catch 12 AM
    if am_pm == 'AM' and hour == 12:
        hour = 0
    if am_pm == 'PM' and hour != 12:
        hour += 12
    return time(hour, minute)


def seconds_until(time_of_day):
    """
    How many seconds between now and a given time_of_day?
    """
    _when = datetime.combine(now(), time_of_day)
    _now = now()
    return abs(_now - _when).seconds
