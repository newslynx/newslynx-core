"""
All utilities related to dates, times, and timezones.
"""


from datetime import datetime, time
from copy import copy

from dateutil import parser
import pytz
import iso8601

from newslynx.lib.regex import re_time
from newslynx.lib.pkg.crontab import CronTab
from newslynx.exc import RequestError


def now(ts=False):
    """
    Get the current datetime / timestamp
    """
    dt = datetime.utcnow()
    dt = dt.replace(tzinfo=pytz.utc)
    if ts:
        return int(dt.strftime("%s"))
    return dt


def floor(dt, unit="hour", value=1, tz=pytz.utc):
    """
    Floor a datetime object. Defaults to using `now`
    """

    if unit not in ['month', 'hour', 'day', 'month']:
        raise ValueError('"unit" must be month, day, hour, or minute')

    second = 0
    minute = copy(dt.minute)
    hour = copy(dt.hour)
    day = copy(dt.day)
    month = copy(dt.month)
    year = copy(dt.year)

    if unit == 'minute':
        minute = dt.minute - (dt.minute % value)

    if unit == 'hour':
        minute = 0
        hour = dt.hour - (dt.hour % value)

    if unit == 'day':
        minute = 0
        hour = 0

    if unit == 'month':
        minute = 0
        hour = 0
        day = 0

    return datetime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        tzinfo=tz
    )


def floor_now(**kw):
    """
    Same as above but with dt set to now()
    """
    return floor(now(), **kw)


def parse_iso(ds, enforce_tz=True):
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

    if enforce_tz:
        raise RequestError('This date is timzeone unaware!')

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


def parse_any(ds, **kw):
    """
    Check for isoformat, timestamp, fallback to dateutil.
    """
    if not ds or not str(ds).strip():
        return

    dt = parse_iso(ds, **kw)
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


def from_struct_time(t, tz=pytz.utc):
    """
    struct_time => datetime.
    """
    return datetime(
        year=t.tm_year,
        month=t.tm_mon,
        day=t.tm_mday,
        hour=t.tm_hour,
        minute=t.tm_min,
        second=t.tm_sec,
        tzinfo=tz
    )


def convert_to_utc(dt):
    """
    Convert a timzeone-aware datetime object to UTC.
    """
    dt = dt.astimezone(pytz.utc)
    dt = dt.replace(tzinfo=pytz.utc)
    return dt


def local(tz):
    """
    Get the current local time for a timezone.
    """
    dt = now()
    tz = pytz.timezone(tz)
    dt = dt.astimezone(tz)
    dt = dt.replace(tzinfo=tz)
    return dt


def force_datetime(dt, tz=None):
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


def valid_tz(tz):
    """
    Validate a timezone.
    """
    return tz in TIMEZONES


def cron(crontab):
    """
    Parse a crontab string and return a CronTab object.
    """
    try:
        return CronTab(crontab)
    except Exception as e:
        raise ValueError(e.message)


def parse_time_of_day(string):
    """
    12:00 AM
    12:00 PM
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


def seconds_until(time_until, now=now()):
    """
    Seconds until a given time.
    """
    when = datetime.combine(now, time_until)
    when = when.replace(tzinfo=now.tzinfo)
    when = when.astimezone(now.tzinfo)
    return abs(now - when).seconds


def time_of_day_to_cron(time_of_day):
    """
    Coerce a time-of-day into cron sytax.
    """
    if not time_of_day:
        return None
    crontab = TIME_OF_DAY_TO_CRON.get(time_of_day)
    return cron(crontab)


# a lookup of human-readable
# times of days to crontab syntax

TIME_OF_DAY_TO_CRON = {
    "12:00 AM": "0 0 * * *",
    "12:30 AM": "30 0 * * *",
    "1:00 AM":  "0 1 * * *",
    "1:30 AM":  "30 1 * * *",
    "2:00 AM":  "0 2 * * *",
    "2:30 AM":  "30 2 * * *",
    "3:00 AM":  "0 3 * * *",
    "3:30 AM":  "30 3 * * *",
    "4:00 AM":  "0 4 * * *",
    "4:30 AM":  "30 4 * * *",
    "5:00 AM":  "0 5 * * *",
    "5:30 AM":  "30 5 * * *",
    "6:00 AM":  "0 6 * * *",
    "6:30 AM":  "30 6 * * *",
    "7:00 AM":  "0 7 * * *",
    "7:30 AM":  "30 7 * * *",
    "8:00 AM":  "0 8 * * *",
    "8:30 AM":  "30 8 * * *",
    "9:00 AM":  "0 9 * * *",
    "9:30 AM":  "30 9 * * *",
    "10:00 AM": "0 10 * * *",
    "10:30 AM": "30 10 * * *",
    "11:00 AM": "0 11 * * *",
    "11:30 AM": "30 11 * * *",
    "12:00 PM": "0 12 * * *",
    "12:30 PM": "30 12 * * *",
    "1:00 PM":  "0 13 * * *",
    "1:30 PM":  "30 13 * * *",
    "2:00 PM":  "0 14 * * *",
    "2:30 PM":  "30 14 * * *",
    "3:00 PM":  "0 15 * * *",
    "3:30 PM":  "30 15 * * *",
    "4:00 PM":  "0 16 * * *",
    "4:30 PM":  "30 16 * * *",
    "5:00 PM":  "0 17 * * *",
    "5:30 PM":  "30 17 * * *",
    "6:00 PM":  "0 18 * * *",
    "6:30 PM":  "30 18 * * *",
    "7:00 PM":  "0 19 * * *",
    "7:30 PM":  "30 19 * * *",
    "8:00 PM":  "0 20 * * *",
    "8:30 PM":  "30 20 * * *",
    "9:00 PM":  "0 21 * * *",
    "9:30 PM":  "30 21 * * *",
    "10:00 PM": "0 22 * * *",
    "10:30 PM": "30 22 * * *",
    "11:00 PM": "0 23 * * *",
    "11:30 PM": "30 23 * * *"
}


TIMEZONES = frozenset([
    "Africa/Abidjan",
    "Africa/Accra",
    "Africa/Addis_Ababa",
    "Africa/Algiers",
    "Africa/Asmara",
    "Africa/Asmera",
    "Africa/Bamako",
    "Africa/Bangui",
    "Africa/Banjul",
    "Africa/Bissau",
    "Africa/Blantyre",
    "Africa/Brazzaville",
    "Africa/Bujumbura",
    "Africa/Cairo",
    "Africa/Casablanca",
    "Africa/Ceuta",
    "Africa/Conakry",
    "Africa/Dakar",
    "Africa/Dar_es_Salaam",
    "Africa/Djibouti",
    "Africa/Douala",
    "Africa/El_Aaiun",
    "Africa/Freetown",
    "Africa/Gaborone",
    "Africa/Harare",
    "Africa/Johannesburg",
    "Africa/Juba",
    "Africa/Kampala",
    "Africa/Khartoum",
    "Africa/Kigali",
    "Africa/Kinshasa",
    "Africa/Lagos",
    "Africa/Libreville",
    "Africa/Lome",
    "Africa/Luanda",
    "Africa/Lubumbashi",
    "Africa/Lusaka",
    "Africa/Malabo",
    "Africa/Maputo",
    "Africa/Maseru",
    "Africa/Mbabane",
    "Africa/Mogadishu",
    "Africa/Monrovia",
    "Africa/Nairobi",
    "Africa/Ndjamena",
    "Africa/Niamey",
    "Africa/Nouakchott",
    "Africa/Ouagadougou",
    "Africa/Porto-Novo",
    "Africa/Sao_Tome",
    "Africa/Timbuktu",
    "Africa/Tripoli",
    "Africa/Tunis",
    "Africa/Windhoek",
    "America/Adak",
    "America/Anchorage",
    "America/Anguilla",
    "America/Antigua",
    "America/Araguaina",
    "America/Argentina/Buenos_Aires",
    "America/Argentina/Catamarca",
    "America/Argentina/ComodRivadavia",
    "America/Argentina/Cordoba",
    "America/Argentina/Jujuy",
    "America/Argentina/La_Rioja",
    "America/Argentina/Mendoza",
    "America/Argentina/Rio_Gallegos",
    "America/Argentina/Salta",
    "America/Argentina/San_Juan",
    "America/Argentina/San_Luis",
    "America/Argentina/Tucuman",
    "America/Argentina/Ushuaia",
    "America/Aruba",
    "America/Asuncion",
    "America/Atikokan",
    "America/Atka",
    "America/Bahia",
    "America/Bahia_Banderas",
    "America/Barbados",
    "America/Belem",
    "America/Belize",
    "America/Blanc-Sablon",
    "America/Boa_Vista",
    "America/Bogota",
    "America/Boise",
    "America/Buenos_Aires",
    "America/Cambridge_Bay",
    "America/Campo_Grande",
    "America/Cancun",
    "America/Caracas",
    "America/Catamarca",
    "America/Cayenne",
    "America/Cayman",
    "America/Chicago",
    "America/Chihuahua",
    "America/Coral_Harbour",
    "America/Cordoba",
    "America/Costa_Rica",
    "America/Creston",
    "America/Cuiaba",
    "America/Curacao",
    "America/Danmarkshavn",
    "America/Dawson",
    "America/Dawson_Creek",
    "America/Denver",
    "America/Detroit",
    "America/Dominica",
    "America/Edmonton",
    "America/Eirunepe",
    "America/El_Salvador",
    "America/Ensenada",
    "America/Fort_Wayne",
    "America/Fortaleza",
    "America/Glace_Bay",
    "America/Godthab",
    "America/Goose_Bay",
    "America/Grand_Turk",
    "America/Grenada",
    "America/Guadeloupe",
    "America/Guatemala",
    "America/Guayaquil",
    "America/Guyana",
    "America/Halifax",
    "America/Havana",
    "America/Hermosillo",
    "America/Indiana/Indianapolis",
    "America/Indiana/Knox",
    "America/Indiana/Marengo",
    "America/Indiana/Petersburg",
    "America/Indiana/Tell_City",
    "America/Indiana/Vevay",
    "America/Indiana/Vincennes",
    "America/Indiana/Winamac",
    "America/Indianapolis",
    "America/Inuvik",
    "America/Iqaluit",
    "America/Jamaica",
    "America/Jujuy",
    "America/Juneau",
    "America/Kentucky/Louisville",
    "America/Kentucky/Monticello",
    "America/Knox_IN",
    "America/Kralendijk",
    "America/La_Paz",
    "America/Lima",
    "America/Los_Angeles",
    "America/Louisville",
    "America/Lower_Princes",
    "America/Maceio",
    "America/Managua",
    "America/Manaus",
    "America/Marigot",
    "America/Martinique",
    "America/Matamoros",
    "America/Mazatlan",
    "America/Mendoza",
    "America/Menominee",
    "America/Merida",
    "America/Metlakatla",
    "America/Mexico_City",
    "America/Miquelon",
    "America/Moncton",
    "America/Monterrey",
    "America/Montevideo",
    "America/Montreal",
    "America/Montserrat",
    "America/Nassau",
    "America/New_York",
    "America/Nipigon",
    "America/Nome",
    "America/Noronha",
    "America/North_Dakota/Beulah",
    "America/North_Dakota/Center",
    "America/North_Dakota/New_Salem",
    "America/Ojinaga",
    "America/Panama",
    "America/Pangnirtung",
    "America/Paramaribo",
    "America/Phoenix",
    "America/Port-au-Prince",
    "America/Port_of_Spain",
    "America/Porto_Acre",
    "America/Porto_Velho",
    "America/Puerto_Rico",
    "America/Rainy_River",
    "America/Rankin_Inlet",
    "America/Recife",
    "America/Regina",
    "America/Resolute",
    "America/Rio_Branco",
    "America/Rosario",
    "America/Santa_Isabel",
    "America/Santarem",
    "America/Santiago",
    "America/Santo_Domingo",
    "America/Sao_Paulo",
    "America/Scoresbysund",
    "America/Shiprock",
    "America/Sitka",
    "America/St_Barthelemy",
    "America/St_Johns",
    "America/St_Kitts",
    "America/St_Lucia",
    "America/St_Thomas",
    "America/St_Vincent",
    "America/Swift_Current",
    "America/Tegucigalpa",
    "America/Thule",
    "America/Thunder_Bay",
    "America/Tijuana",
    "America/Toronto",
    "America/Tortola",
    "America/Vancouver",
    "America/Virgin",
    "America/Whitehorse",
    "America/Winnipeg",
    "America/Yakutat",
    "America/Yellowknife",
    "Antarctica/Casey",
    "Antarctica/Davis",
    "Antarctica/DumontDUrville",
    "Antarctica/Macquarie",
    "Antarctica/Mawson",
    "Antarctica/McMurdo",
    "Antarctica/Palmer",
    "Antarctica/Rothera",
    "Antarctica/South_Pole",
    "Antarctica/Syowa",
    "Antarctica/Troll",
    "Antarctica/Vostok",
    "Arctic/Longyearbyen",
    "Asia/Aden",
    "Asia/Almaty",
    "Asia/Amman",
    "Asia/Anadyr",
    "Asia/Aqtau",
    "Asia/Aqtobe",
    "Asia/Ashgabat",
    "Asia/Ashkhabad",
    "Asia/Baghdad",
    "Asia/Bahrain",
    "Asia/Baku",
    "Asia/Bangkok",
    "Asia/Beirut",
    "Asia/Bishkek",
    "Asia/Brunei",
    "Asia/Calcutta",
    "Asia/Choibalsan",
    "Asia/Chongqing",
    "Asia/Chungking",
    "Asia/Colombo",
    "Asia/Dacca",
    "Asia/Damascus",
    "Asia/Dhaka",
    "Asia/Dili",
    "Asia/Dubai",
    "Asia/Dushanbe",
    "Asia/Gaza",
    "Asia/Harbin",
    "Asia/Hebron",
    "Asia/Ho_Chi_Minh",
    "Asia/Hong_Kong",
    "Asia/Hovd",
    "Asia/Irkutsk",
    "Asia/Istanbul",
    "Asia/Jakarta",
    "Asia/Jayapura",
    "Asia/Jerusalem",
    "Asia/Kabul",
    "Asia/Kamchatka",
    "Asia/Karachi",
    "Asia/Kashgar",
    "Asia/Kathmandu",
    "Asia/Katmandu",
    "Asia/Khandyga",
    "Asia/Kolkata",
    "Asia/Krasnoyarsk",
    "Asia/Kuala_Lumpur",
    "Asia/Kuching",
    "Asia/Kuwait",
    "Asia/Macao",
    "Asia/Macau",
    "Asia/Magadan",
    "Asia/Makassar",
    "Asia/Manila",
    "Asia/Muscat",
    "Asia/Nicosia",
    "Asia/Novokuznetsk",
    "Asia/Novosibirsk",
    "Asia/Omsk",
    "Asia/Oral",
    "Asia/Phnom_Penh",
    "Asia/Pontianak",
    "Asia/Pyongyang",
    "Asia/Qatar",
    "Asia/Qyzylorda",
    "Asia/Rangoon",
    "Asia/Riyadh",
    "Asia/Saigon",
    "Asia/Sakhalin",
    "Asia/Samarkand",
    "Asia/Seoul",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Asia/Taipei",
    "Asia/Tashkent",
    "Asia/Tbilisi",
    "Asia/Tehran",
    "Asia/Tel_Aviv",
    "Asia/Thimbu",
    "Asia/Thimphu",
    "Asia/Tokyo",
    "Asia/Ujung_Pandang",
    "Asia/Ulaanbaatar",
    "Asia/Ulan_Bator",
    "Asia/Urumqi",
    "Asia/Ust-Nera",
    "Asia/Vientiane",
    "Asia/Vladivostok",
    "Asia/Yakutsk",
    "Asia/Yekaterinburg",
    "Asia/Yerevan",
    "Atlantic/Azores",
    "Atlantic/Bermuda",
    "Atlantic/Canary",
    "Atlantic/Cape_Verde",
    "Atlantic/Faeroe",
    "Atlantic/Faroe",
    "Atlantic/Jan_Mayen",
    "Atlantic/Madeira",
    "Atlantic/Reykjavik",
    "Atlantic/South_Georgia",
    "Atlantic/St_Helena",
    "Atlantic/Stanley",
    "Australia/ACT",
    "Australia/Adelaide",
    "Australia/Brisbane",
    "Australia/Broken_Hill",
    "Australia/Canberra",
    "Australia/Currie",
    "Australia/Darwin",
    "Australia/Eucla",
    "Australia/Hobart",
    "Australia/LHI",
    "Australia/Lindeman",
    "Australia/Lord_Howe",
    "Australia/Melbourne",
    "Australia/North",
    "Australia/NSW",
    "Australia/Perth",
    "Australia/Queensland",
    "Australia/South",
    "Australia/Sydney",
    "Australia/Tasmania",
    "Australia/Victoria",
    "Australia/West",
    "Australia/Yancowinna",
    "Brazil/Acre",
    "Brazil/DeNoronha",
    "Brazil/East",
    "Brazil/West",
    "Canada/Atlantic",
    "Canada/Central",
    "Canada/East-Saskatchewan",
    "Canada/Eastern",
    "Canada/Mountain",
    "Canada/Newfoundland",
    "Canada/Pacific",
    "Canada/Saskatchewan",
    "Canada/Yukon",
    "CET",
    "Chile/Continental",
    "Chile/EasterIsland",
    "CST6CDT",
    "Cuba",
    "EET",
    "Egypt",
    "Eire",
    "EST",
    "EST5EDT",
    "Etc/GMT",
    "Etc/GMT+0",
    "Etc/GMT+1",
    "Etc/GMT+10",
    "Etc/GMT+11",
    "Etc/GMT+12",
    "Etc/GMT+2",
    "Etc/GMT+3",
    "Etc/GMT+4",
    "Etc/GMT+5",
    "Etc/GMT+6",
    "Etc/GMT+7",
    "Etc/GMT+8",
    "Etc/GMT+9",
    "Etc/GMT-0",
    "Etc/GMT-1",
    "Etc/GMT-10",
    "Etc/GMT-11",
    "Etc/GMT-12",
    "Etc/GMT-13",
    "Etc/GMT-14",
    "Etc/GMT-2",
    "Etc/GMT-3",
    "Etc/GMT-4",
    "Etc/GMT-5",
    "Etc/GMT-6",
    "Etc/GMT-7",
    "Etc/GMT-8",
    "Etc/GMT-9",
    "Etc/GMT0",
    "Etc/Greenwich",
    "Etc/UCT",
    "Etc/Universal",
    "Etc/UTC",
    "Etc/Zulu",
    "Europe/Amsterdam",
    "Europe/Andorra",
    "Europe/Athens",
    "Europe/Belfast",
    "Europe/Belgrade",
    "Europe/Berlin",
    "Europe/Bratislava",
    "Europe/Brussels",
    "Europe/Bucharest",
    "Europe/Budapest",
    "Europe/Busingen",
    "Europe/Chisinau",
    "Europe/Copenhagen",
    "Europe/Dublin",
    "Europe/Gibraltar",
    "Europe/Guernsey",
    "Europe/Helsinki",
    "Europe/Isle_of_Man",
    "Europe/Istanbul",
    "Europe/Jersey",
    "Europe/Kaliningrad",
    "Europe/Kiev",
    "Europe/Lisbon",
    "Europe/Ljubljana",
    "Europe/London",
    "Europe/Luxembourg",
    "Europe/Madrid",
    "Europe/Malta",
    "Europe/Mariehamn",
    "Europe/Minsk",
    "Europe/Monaco",
    "Europe/Moscow",
    "Europe/Nicosia",
    "Europe/Oslo",
    "Europe/Paris",
    "Europe/Podgorica",
    "Europe/Prague",
    "Europe/Riga",
    "Europe/Rome",
    "Europe/Samara",
    "Europe/San_Marino",
    "Europe/Sarajevo",
    "Europe/Simferopol",
    "Europe/Skopje",
    "Europe/Sofia",
    "Europe/Stockholm",
    "Europe/Tallinn",
    "Europe/Tirane",
    "Europe/Tiraspol",
    "Europe/Uzhgorod",
    "Europe/Vaduz",
    "Europe/Vatican",
    "Europe/Vienna",
    "Europe/Vilnius",
    "Europe/Volgograd",
    "Europe/Warsaw",
    "Europe/Zagreb",
    "Europe/Zaporozhye",
    "Europe/Zurich",
    "GB",
    "GB-Eire",
    "GMT",
    "GMT+0",
    "GMT-0",
    "GMT0",
    "Greenwich",
    "Hongkong",
    "HST",
    "Iceland",
    "Indian/Antananarivo",
    "Indian/Chagos",
    "Indian/Christmas",
    "Indian/Cocos",
    "Indian/Comoro",
    "Indian/Kerguelen",
    "Indian/Mahe",
    "Indian/Maldives",
    "Indian/Mauritius",
    "Indian/Mayotte",
    "Indian/Reunion",
    "Iran",
    "Israel",
    "Jamaica",
    "Japan",
    "Kwajalein",
    "Libya",
    "MET",
    "Mexico/BajaNorte",
    "Mexico/BajaSur",
    "Mexico/General",
    "MST",
    "MST7MDT",
    "Navajo",
    "NZ",
    "NZ-CHAT",
    "Pacific/Apia",
    "Pacific/Auckland",
    "Pacific/Chatham",
    "Pacific/Chuuk",
    "Pacific/Easter",
    "Pacific/Efate",
    "Pacific/Enderbury",
    "Pacific/Fakaofo",
    "Pacific/Fiji",
    "Pacific/Funafuti",
    "Pacific/Galapagos",
    "Pacific/Gambier",
    "Pacific/Guadalcanal",
    "Pacific/Guam",
    "Pacific/Honolulu",
    "Pacific/Johnston",
    "Pacific/Kiritimati",
    "Pacific/Kosrae",
    "Pacific/Kwajalein",
    "Pacific/Majuro",
    "Pacific/Marquesas",
    "Pacific/Midway",
    "Pacific/Nauru",
    "Pacific/Niue",
    "Pacific/Norfolk",
    "Pacific/Noumea",
    "Pacific/Pago_Pago",
    "Pacific/Palau",
    "Pacific/Pitcairn",
    "Pacific/Pohnpei",
    "Pacific/Ponape",
    "Pacific/Port_Moresby",
    "Pacific/Rarotonga",
    "Pacific/Saipan",
    "Pacific/Samoa",
    "Pacific/Tahiti",
    "Pacific/Tarawa",
    "Pacific/Tongatapu",
    "Pacific/Truk",
    "Pacific/Wake",
    "Pacific/Wallis",
    "Pacific/Yap",
    "Poland",
    "Portugal",
    "posixrules",
    "PRC",
    "PST8PDT",
    "ROC",
    "ROK",
    "Singapore",
    "Turkey",
    "UCT",
    "Universal",
    "US/Alaska",
    "US/Aleutian",
    "US/Arizona",
    "US/Central",
    "US/East-Indiana",
    "US/Eastern",
    "US/Hawaii",
    "US/Indiana-Starke",
    "US/Michigan",
    "US/Mountain",
    "US/Pacific",
    "US/Pacific-New",
    "US/Samoa",
    "UTC",
    "W-SU",
    "WET",
    "Zulu"
])
