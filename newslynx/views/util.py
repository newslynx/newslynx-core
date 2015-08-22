import os
import importlib
import math
from urlparse import urljoin
import re

from flask import request, Response, url_for
from flask import Blueprint

from newslynx.core import db
from newslynx.exc import NotFoundError, RequestError
from newslynx.lib import dates
from newslynx.lib.serialize import json_to_obj, jsonify
from newslynx.core import settings
from newslynx.models.util import get_table_columns
from newslynx.constants import *


RE_HEX_CODE = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')


# Blueprints

def register_blueprints(app, *mods):
    """
    List all Blueprint instances underneath
    specified modules and register them.
    """
    for mod in mods:
        package_name = mod.__name__
        package_path = mod.__path__[0]
        for fp in os.listdir(package_path):
            if (not fp.endswith('.pyc') and
                    '__init__' not in fp and
                    'templates' not in fp):

                name = fp.replace('.py', '')
                # try:
                m = importlib.import_module(
                    '%s.%s' % (package_name, name))
                # except:
                #     continue
                for item in dir(m):
                    item = getattr(m, item)
                    if isinstance(item, Blueprint):
                        app.register_blueprint(item)

# Arguments


def arg_str(name, default=None):
    """ Fetch a query argument, as a string. """
    v = request.args.get(name, '')
    if not len(v):
        return default
    return v


def arg_int(name, default=None):
    """ Fetch a query argument, as an integer. """
    v = request.args.get(name, '')
    if not len(v):
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        raise RequestError('Invalid value for "{}". '
                           'It should be an integer.'
                           .format(name))


def arg_float(name, default=None):
    """ Fetch a query argument, as a float. """
    v = request.args.get(name, '')
    try:
        v = request.args.get(name)
        return float(v)
    except (ValueError, TypeError):
        raise RequestError('Invalid value for "{}". '
                           'It should be a float.'
                           .format(name))


def arg_bool(name, default=False):
    """ Fetch a query argument, as a boolean. """
    v = request.args.get(name, '')
    if not len(v):
        return default
    if v.lower() in TRUE_VALUES:
        return True
    if v.lower() in FALSE_VALUES:
        return False
    return default


def arg_date(name, default=None):
    """ Fetch a query argument, as a datetime object."""
    v = request.args.get(name, '')
    if not len(v):
        return default
    v = dates.parse_iso(v)
    if not v:
        raise RequestError('Invalid value for "{}". '
                           'It should be an iso8601 datetime string.'
                           .format(name))
    return v


def arg_limit(name='per_page', default=25):
    """ Get a limit argument. """
    return max(1, min(100, arg_int(name, default=default)))


def arg_list(name, default=None, typ=str, exclusions=False):
    """ get a comma-separated list of args, asserting a type.
    includes the ability to parse out exclusions via '!' or '-' prefix"""

    type_string = str(typ).split("'")[1]
    include_values = []
    exclude_values = []

    vv = arg_str(name, default=None)
    if not vv:
        if exclusions:
            return default, default
        return default

    for i, value in enumerate(vv.split(','), start=1):

        if value.startswith('!') or value.startswith('-'):
            value = value[1:]
            exclude = True

        else:
            exclude = False

        try:

            if 'date' in type_string:
                v = dates.parse_iso(value)
                if not v:
                    raise ValueError

            else:
                v = typ(value)

        except:
            raise RequestError(
                '"{}", element  {} of "{}" is invalid. '
                'It should be a {} type.'
                .format(value, i, name, type_string))

        if exclusions:
            if exclude:
                exclude_values.append(v)

            else:
                include_values.append(v)

        else:
            include_values.append(v)

    if exclusions:
        return include_values, exclude_values

    return include_values


def arg_sort(name, default=None):
    """
    Fetch a query argument for a sort field,
    checking if we should sort asc / desc, as a float.
    """
    direction = 'asc'
    v = arg_str(name, default)
    if v:
        if v.startswith('-'):
            v = v[1:]
            direction = 'desc'
    return v, direction


# post / put data.


def request_data():
    """
    Fetch request data from json / form / raw json string.
    """
    data = request.get_json(silent=True)
    if data is None:
        try:
            data = json_to_obj(request.data)
        except:
            data = None
    if data is None:
        data = dict(request.form.items())
    return data


def listify_data_arg(name):
    """
    Allow for multiple list formats of
    data args including:
        - comma-separated list of ids
        - list of ids
        - list of dicts with an id key
    """
    value = request_data().get(name)
    if not value:
        return []

    if not isinstance(value, list):
        if ',' in value:
            value = [v.strip() for v in value.split(',')]
        else:
            value = [value]

    if isinstance(value[0], dict):
        try:
            value = [a['id'] for a in value]
        except KeyError:
            raise RequestError(
                "When passing in a dictionary or list of dictionaries "
                "to '{}', they must contain a key with the name 'id'"
                .format(name))
    return value


# Validation


def validate_fields(obj, fields=[], incl=[], suffix='to select by'):
    """
    check a list of fields against column names.
    """
    columns = get_table_columns(obj, incl)
    bad_fields = []
    for field in fields:
        if field not in columns:
            bad_fields.append(field)

    if len(bad_fields):
        if len(bad_fields) == 1:
            msg = 'is not a valid field name'
        else:
            msg = 'are not valid field names'
        raise RequestError(
            "'{}' {} {}. Choose from: {}."
            .format(', '.join(bad_fields), msg, suffix, ", ".join(columns)))


def validate_tag_types(values):
    """
    check a list of values against tag types.
    """
    if not isinstance(values, list):
        values = [values]
    bad_values = []
    for value in values:
        if value not in TAG_TYPES:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid tag type'
        else:
            msg = 'are not valid tag types'
        raise RequestError(
            "'{}' {}. Choose from:"
            .format(', '.join(bad_values), msg, IMPACT_TAG_TYPES))


def validate_tag_categories(values):
    """
    check a list of values against column names.
    """
    if not isinstance(values, list):
        values = [values]
    bad_values = []
    for field in values:
        if field not in IMPACT_TAG_CATEGORIES:
            bad_values.append(field)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid tag category.'
        else:
            msg = 'are not valid tag categories.'
        raise RequestError(
            "'{}' {}. Choose from: {}"
            .format(', '.join(bad_values), msg, IMPACT_TAG_CATEGORIES))


def validate_tag_levels(values):
    """
    check a list of values against tag levels.
    """
    if not isinstance(values, list):
        values = [values]
    bad_values = []
    for value in values:
        if value not in IMPACT_TAG_LEVELS:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid tag level.'
        else:
            msg = 'are not valid tag levels.'
        raise RequestError(
            "'{}' {}. Choose from: {}."
            .format(', '.join(bad_values), msg, IMPACT_TAG_LEVELS))


def validate_content_item_types(values):
    """
    check a list of values against ContentItem types.
    """
    if not isinstance(values, list):
        values = [values]
    bad_values = []
    types = CONTENT_ITEM_TYPES + ['all']
    for value in values:
        if value not in types:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid ContentItem type.'
        else:
            msg = 'are not valid ContentItem types.'
        raise RequestError(
            "'{}' {}. Choose from: {}."
            .format(', '.join(bad_values), msg, types))


def validate_event_status(value):
    """
    check a list of values against event statuses.
    """
    statuses = EVENT_STATUSES + ['all']
    if value not in statuses:
        raise RequestError(
            "'{}' is not a valid Event status. Choose from {}."
            .format(value, statuses))


def validate_event_search_vector(value):
    """
    check a list of values against event statuses.
    """
    search_vector = EVENT_SEARCH_VECTORS
    if value not in search_vector:
        raise RequestError(
            "'{}' is not a valid Event search vector. Choose from {}."
            .format(value, search_vector))


def validate_event_provenances(value):
    """
    check a list of values against event provenances.
    """
    if not value:
        return
    provenances = EVENT_PROVENANCES
    if value not in provenances:
        raise RequestError(
            "'{}' is not a valid Event provenance. Choose from {}."
            .format(value, provenances))


def validate_event_facets(values):
    """
    check a list of values against ContentItem types.
    """
    if not isinstance(values, list):
        values = [values]
    facets = EVENT_FACETS + ['all']
    bad_values = []
    for value in values:
        if value not in facets:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid Event facet.'
        else:
            msg = 'are not valid Event facets.'
        raise RequestError(
            "'{}' {}. Choose from: {}."
            .format(', '.join(bad_values), msg, facets))


def validate_content_item_facets(values):
    """
    check a list of values against ContentItem types.
    """
    if not isinstance(values, list):
        values = [values]
    facets = CONTENT_ITEM_FACETS + ['all']
    bad_values = []
    for value in values:
        if value not in facets:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid ContentItem facet.'
        else:
            msg = 'are not valid ContentItem facets.'
        raise RequestError(
            "'{}' {}. Choose from: {}."
            .format(', '.join(bad_values), msg, facets))


def validate_content_item_provenances(value):
    """
    check a list of values against ContentItem provenances.
    """
    if not value:
        return
    provenances = CONTENT_ITEM_PROVENANCES
    if value not in provenances:
        raise RequestError(
            "'{}' is not a valid ContentItem provenance. Choose from {}."
            .format(value, provenances))


def validate_sous_chef_creates(values):
    """
    check a list of values against ContentItem types.
    """
    if not isinstance(values, list):
        values = [values]
    facets = SOUS_CHEF_CREATES + ['all']
    bad_values = []
    for value in values:
        if value not in facets:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid collection a SousChef creates.'
        else:
            msg = 'are not valid ContentItem facets.'
        raise RequestError("'{}' {}. Choose from: {}."
                           .format(', '.join(bad_values), msg, facets))


def validate_content_item_search_vector(value):
    """
    check a list of values against event statuses.
    """
    search_vector = CONTENT_ITEM_SEARCH_VECTORS
    if value not in search_vector:
        raise RequestError(
            "'{}' is not a valid Event search vector. Choose from {}."
            .format(value, search_vector))


def validate_hex_code(value):
    """
    check a list of values against ContentItem types.
    """
    if not RE_HEX_CODE.search(value):
        raise RequestError("'{}' is not a valid hex code.".format(value))


def validate_ts_unit(value):
    """
    check a list of values against ContentItem types.
    """
    # check for null here.
    if value in NULL_VALUES:
        value = None
    if value not in METRIC_TS_UNITS:
        raise RequestError(
            "'{}' is not a valid timeseries unit. Choose from {}."
            .format(value, METRIC_TS_UNITS))
    return value


def validate_recipe_statuses(values):
    """
    Validate recipe statuses.
    """
    if not isinstance(values, list):
        values = [values]
    statuses = RECIPE_STATUSES
    bad_values = []
    for value in values:
        if value not in statuses:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid Recipe status'
        else:
            msg = 'are not valid Recipe statuses'
        raise RequestError("'{}' {}. Choose from: {}."
                           .format(', '.join(bad_values), msg, ", ".join(statuses)))


def validate_recipe_schedule_types(values):
    """
    Validate recipe statuses.
    """
    if not isinstance(values, list):
        values = [values]
    statuses = RECIPE_SCHEDULE_TYPES
    bad_values = []
    for value in values:
        if value not in statuses:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid Recipe schedule type'
        else:
            msg = 'are not valid Recipe schedule type'
        raise RequestError("'{}' {}. Choose from: {}."
                           .format(', '.join(bad_values), msg, ", ".join(statuses)))


def validate_metric_levels(values):
    """
    Validate metric levels.
    """
    if not isinstance(values, list):
        values = [values]
    bad_values = []
    for value in values:
        if value not in METRIC_LEVELS:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid Metric level.'
        else:
            msg = 'are not valid Metric levels'
        raise RequestError(
            "'{}' {}. Choose from: {}."
            .format(', '.join(bad_values), msg, ", ".join(METRIC_LEVELS)))


def validate_metric_aggregations(values):
    """
    Validate metric aggregations
    """
    if not isinstance(values, list):
        values = [values]
    bad_values = []
    for value in values:
        if value not in METRIC_AGGREGATIONS:
            bad_values.append(value)

    if len(bad_values):
        if len(bad_values) == 1:
            msg = 'is not a valid Metric aggregation.'
        else:
            msg = 'are not valid Metric aggregations'
        raise RequestError(
            "'{}' {}. Choose from: {}."
            .format(', '.join(bad_values), msg, ", ".join(METRIC_AGGREGATIONS)))


# Pagination

def urls_for_pagination(handler, total_results, **kw):
    """
    Generate pagination urls.
    """

    # parse pagination args
    per_page = arg_limit('per_page')
    page = arg_int('page', 1)
    total_pages = int(math.ceil(total_results / float(per_page)))

    p = dict(page=page, per_page=per_page, total_pages=total_pages)

    # if we're on the first page, only provide a 'next' url.
    if page < 2:
        kw['page'] = 2
        p['next'] = urljoin(settings.API_URL, url_for(handler, **kw))

    else:
        kw['page'] = page + 1
        p['next'] = urljoin(settings.API_URL, url_for(handler, **kw))

        kw['page'] = page - 1
        p['prev'] = urljoin(settings.API_URL, url_for(handler, **kw))

    # if we're on the final page,
    if page >= total_pages:
        p.pop('next')

    # always include first and last pages
    kw['page'] = 1
    p['first'] = urljoin(settings.API_URL, url_for(handler, **kw))

    kw['page'] = total_pages
    p['last'] = urljoin(settings.API_URL, url_for(handler, **kw))

    return p


def url_for_job_status(**kw):
    """
    Generate a url for a job status
    """
    # add context
    kw['orig_url'] = request.url
    kw['started'] = dates.now().isoformat()
    path = url_for('jobs.get_status', **kw)
    kw['status_url'] = urljoin(settings.API_URL, path)
    return kw


# Responses

def delete_response():
    """
    Return an empty response from a delete request
    with the proper status code.
    """
    r = Response()
    r.status_code = 204
    return r


def error_response(name, err):
    """
    Return an empty response from a delete request
    with the proper status code.
    """
    resp = {
        "error": name,
        "message": err.message,
        "status_code": err.status_code
    }
    response = jsonify(resp)
    response.status_code = err.status_code
    return response


def obj_or_404(obj, message):
    """
    Raise 404 if no object is present.
    """
    if obj is None:
        raise NotFoundError(message)


# Localization
def localize(org):
    """
    Localize a session to an org's settings.
    """
    _localize = arg_bool('localize', default=False)
    if _localize:
        db.session.execute("SET TIMEZONE TO '{}'".format(org.timezone))
    else:
        db.session.execute("SET TIMEZONE TO UTC")
