"""
All utilities related to dates, times, and timezones.
"""
from datetime import datetime, time

from dateutil import parser
import pytz
import iso8601

from newslynx.lib.regex import re_time


def now(ts=False):
    """
    Get the current datetime / timestamp
    """
    dt = datetime.utcnow()
    dt = dt.replace(tzinfo=pytz.utc)
    if ts:
        return int(dt.strftime('%s'))
    return dt


def parse_iso(ds):
    """
    parse an isodate/datetime string with or without
    a datestring.  Convert timzeone aware datestrings
    to UTC.
    """

    try:
        dt = iso8601.parse_date(ds)
    except:
        return None

    tz = getattr(dt, 'tzinfo', None)
    if tz:
        dt = force_datetime(dt, tz=tz)
        return convert_to_utc(dt)

    return force_datetime(dt, tz=pytz.utc)


def parse_ts(ts):
    """
    Get a datetime object from a utctimestamp.
    """
    # validate
    if not len(str(ts)) >= 10 and str(ts).startswith('1'):
        return
    if not isinstance(ts, float):
        try:
            ts = float(ts)
        except ValueError:
            return
    dt = datetime.utcfromtimestamp(ts)
    dt = dt.replace(tzinfo=pytz.utc)
    return dt


def parse_any(ds):
    """
    Check for isoformat, timestamp, fallback to dateutil.
    """
    if not ds or not str(ds).strip():
        return

    dt = parse_iso(ds)
    if dt:
        return dt

    dt = parse_ts(ds)
    if dt:
        return dt
    try:
        dt = parser.parse(ds)
    except ValueError:
        return

    # convert to UTC
    tz = getattr(dt, 'tzinfo', None)
    if tz:
        dt = force_datetime(dt, tz=tz)
        return convert_to_utc(dt)

    return force_datetime(dt, tz=pytz.utc)


def convert_to_utc(dt):
    """
    Convert a timzeone-aware datetime object to UTC.
    """
    dt = dt.astimezone(pytz.utc)
    dt = dt.replace(tzinfo=pytz.utc)
    return dt


def force_datetime(dt, tz):
    """
    Force a datetime.date into a datetime obj
    """
    return datetime(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=getattr(dt, 'hour', 0),
        minute=getattr(dt, 'minute',  0,),
        second=getattr(dt, 'second', 0),
        tzinfo=tz
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
