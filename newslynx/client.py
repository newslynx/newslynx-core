import os
import copy
from inspect import isgenerator
import time

import requests
from requests import Session, Request
from urlparse import urljoin

from newslynx import settings
from newslynx.lib.serialize import obj_to_json, json_to_obj
from newslynx.exc import ERRORS, ClientError, JobError
from newslynx.logs import log


RET_CODES = [200, 201, 202]
GOOD_CODES = RET_CODES + [204]


class BaseClient(object):

    """
    A base client for each endpoint to inherit from.
    """

    def __init__(self, **kw):

        # defaults / helpers
        self._url = kw.pop('url', settings.API_URL)

        # standardize url
        if not self._url.endswith('/'):
            self._url += '/'

        self.apikey = kw.get('apikey', os.getenv('NEWSLYNX_API_KEY'))
        self.org = kw.pop('org', os.getenv('NEWSLYNX_API_ORG_ID'))
        self._version = kw.pop('version', 'v1')
        self._endpoint = self._url + 'api/' + self._version + "/"

        # establish session
        self._session = Session()

    def _format_url(self, *args):
        """
        Add segments to endpoint to form a URL.
        """

        path = "/".join([str(a) for a in args])
        return urljoin(self._endpoint, path)

    def _request(self, method, url, **kw):
        """
        A wrapper for all request executions.
        """
        if not url.endswith('login') and not self.apikey:
            raise ClientError('You haven\'t set your apikey or logged in yet!')

        # add params to kw
        kw.setdefault('params', {})

        # add apikey/org when required or set by user.
        kw['params'].update({'apikey': self.apikey})
        if 'org' not in kw['params']:
            kw['params']['org'] = self.org

        # orgs endpoint doesn't require org
        if url.startswith(self._format_url('orgs')):
            kw['params'].pop('org')

        # dump json
        if kw.get('data'):
            kw['data'] = obj_to_json(kw['data'])

        # execute
        r = Request(method, url, **kw)

        try:
            resp = self._session.send(r.prepare())
            err = None

        except Exception as e:
            err = e
            resp = None

        # handle errors
        self._handle_errors(resp, err)

        # format response
        return self._format_response(resp)

    def _split_auth_params_from_data(self, kw, kw_incl=[]):
        params = {}
        if 'apikey' in kw:
            params['apikey'] = kw.pop('apikey')

        if 'org' in kw:
            params['org'] = kw.pop('org')

        if 'localize' in kw:
            params['localize'] = kw.pop('localize')

        for i in kw_incl:
            if i in kw:
                params[i] = kw.pop(i)

        return kw, params

    def _check_bulk_kw(self, kw):
        """
        Validate bulk endpoints.
        """
        if 'data' not in kw:
            raise ClientError(
                'Bulk endpoints require a "data" keyword argument.')
        if isgenerator(kw['data']):
            kw['data'] = list(kw['data'])
        return kw

    def _handle_errors(self, resp, err=None):
        """
        Handle all errors.
        """
        if err:
            raise err

        # check status codes
        elif resp.status_code not in GOOD_CODES:
            try:
                d = resp.json()
            except:
                raise ClientError(resp.content)

            err = ERRORS.get(d['error'])
            if not err:
                raise ClientError(resp.content)
            raise err(d['message'])

    def _format_response(self, resp):
        """
        Format a response with addict.Dict
        """

        # if there's no response just return true.
        if resp.status_code == 204:
            return True
        return resp.json()

    def login(self, **kw):
        """
        Login via email + password.
        """
        url = self._format_url('login')
        resp = self._request('POST', url, data=kw)
        return resp


class Me(BaseClient):

    def get(self, **kw):
        """
        Fetch your user profile.
        """

        url = self._format_url('me')
        return self._request('GET', url, params=kw)

    def update(self, **kw):
        """
        Update your user profile.
        """
        kw, params = self._split_auth_params_from_data(
            kw, kw_incl=['refresh_apikey'])

        # special case for this parameter

        url = self._format_url('me')
        return self._request('PUT', url, data=kw, params=params)

    def orgs(self, **kw):
        """
        Get orgs you have access to.
        """
        url = self._format_url('orgs')
        return self._request('GET', url, params=kw)


class Orgs(BaseClient):

    def list(self, **kw):
        """
        List organizations you have access to.
        """
        url = self._format_url('orgs')
        return self._request('GET', url, params=kw)

    def get(self, org=None, **kw):
        """
        Get an organization.
        """
        org = self._check_org(org)
        url = self._format_url('orgs', org)
        return self._request('GET', url, params=kw)

    def create(self, **kw):
        """
        Create an organization.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('orgs')
        return self._request('POST', url, data=kw, params=params)

    def update(self, org=None, **kw):
        """
        Update an organization.
        """
        org = self._check_org(org)
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('orgs', org)
        return self._request('PUT', url, data=kw, params=params)

    def delete(self, org=None, **kw):
        """
        Delete an organization.
        """
        org = self._check_org(org)
        url = self._format_url('orgs', org)
        return self._request('DELETE', url, params=kw)

    def get_user(self, org=None, user=None, **kw):
        """
        Get a user profile from an organization
        """
        org = self._check_org(org)
        if not user:
            raise ValueError(
                'You must pass in the user id or email as the second argument.')

        url = self._format_url('orgs', org, 'users', user)
        return self._request('GET', url, params=kw)

    def list_users(self, org=None, **kw):
        """
        Get all user profiles under an organization.
        """
        org = self._check_org(org)
        url = self._format_url('orgs', org, 'users')
        return self._request('GET', url, params=kw)

    def create_user(self, org=None, **kw):
        """
        Create a user under an org.
        """
        org = self._check_org(org)
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('orgs', org, 'users')
        return self._request('POST', url, data=kw, params=params)

    def add_user(self, org=None, user=None, **kw):
        """
        Add an existing user to an organization.
        """
        org = self._check_org(org)
        url = self._format_url('orgs', org, 'users', user)
        if not user:
            raise ValueError(
                'You must pass in the \'user\' id or email as the second argument.')
        return self._request('PUT', url, params=kw)

    def remove_user(self, org=None, user=None, **kw):
        """
        Remove an existing user from an organization.
        """
        org = self._check_org(org)
        if not user:
            raise ValueError(
                'You must pass in the \'user\' id or email as the second argument.')
        url = self._format_url('orgs', org, 'users', user)
        return self._request('DELETE', url, params=kw)

    def get_timeseries(self, org=None, **kw):
        """
        Get a content item timeseries.
        """
        org = self._check_org(org)
        url = self._format_url('orgs', org, 'timeseries')
        return self._request('GET', url, params=kw)

    def create_timeseries(self, org=None, **kw):
        """
        Create timeseries metric(s) for a content item.
        """
        org = self._check_org(org)
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('orgs', org, 'timeseries')
        return self._request('POST', url, params=params, data=kw)

    def bulk_create_timeseries(self, org=None, **kw):
        """
        Bulk create timeseries metric(s) for content items.
        """
        org = self._check_org(org)
        kw = self._check_bulk_kw(kw)
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('orgs', org, 'timeseries', 'bulk')
        return self._request('POST', url, params=params, data=kw['data'])

    def get_summary(self, org=None, **kw):
        """
        Get an org's summary metrics.
        """
        org = self._check_org(org)
        url = self._format_url('orgs', org, 'summary')
        return self._request('GET', url, params=kw)

    def create_summary(self, org=None, **kw):
        """
        Create summary metric(s) for an organization.
        """
        org = self._check_org(org)
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('orgs', org, 'summary')
        return self._request('POST', url, params=params, data=kw)

    def simple_content(self, org=None, **kw):
        """
        Return a simplified, non-paginated list of all content items for an org.
        This is mostly useful for recipes.
        """
        org = self._check_org(org)
        url = self._format_url('orgs', org, 'simple-content')
        return self._request('GET', url, params=kw)

    def _check_org(self, org):
        """
        Check for org arg.
        """
        if not org:
            org = copy.copy(self.org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or slug as the first argument '
                    'if you have not set it when initializating API.')
        return org


class Settings(BaseClient):

    def list(self, **kw):
        """
        Add/update a setting for an organization.
        """

        url = self._format_url('settings')
        return self._request('GET', url, params=kw)

    def get(self, name_id, **kw):
        """
        Get a particular setting.
        """

        url = self._format_url('settings', name_id)
        return self._request('GET', url, **kw)

    def create(self, **kw):
        """
        Create a setting
        """
        # jsonify value
        if kw.get('json_value', True):
            if not isinstance(kw.get('value'), basestring):
                kw['value'] = obj_to_json(kw['value'])

        kw, params = self._split_auth_params_from_data(kw)

        url = self._format_url('settings')
        return self._request('POST', url, data=kw, params=params)

    def update(self, name_id, **kw):
        """
        Update a setting
        """
        # jsonify value
        if kw.get('json_value', True):
            if not isinstance(kw.get('value'), basestring):
                kw['value'] = obj_to_json(kw['value'])

        kw, params = self._split_auth_params_from_data(kw)

        url = self._format_url('settings', name_id)
        return self._request('PUT', url, data=kw, params=params)

    def delete(self, name_id, **kw):
        """
        Delete a setting.
        """

        url = self._format_url('settings', name_id)
        return self._request('DELETE', url, params=kw)


class Tags(BaseClient):

    def list(self, **kw):
        """
        Get all tags
        """
        url = self._format_url('tags')
        return self._request('GET', url, params=kw)

    def create(self, **kw):
        """
        Create a tag
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('tags')
        return self._request('POST', url, data=kw, params=params)

    def get(self, tag_id, **kw):
        """
        Get a tag
        """
        url = self._format_url('tags', tag_id)
        return self._request('GET', url, data=kw, params=kw)

    def update(self, tag_id, **kw):
        """
        Update a tag
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('tags', tag_id)
        return self._request('PUT', url, data=kw, params=params)

    def delete(self, tag_id, **kw):
        """
        Delete a tag
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('tags', tag_id)
        return self._request('DELETE', url, params=kw)


class Recipes(BaseClient):

    def list(self, **kw):
        """
        Get all recipes / facets.
        """
        url = self._format_url('recipes')
        return self._request('GET', url, params=kw)

    def create(self, **kw):
        """
        Create a recipe
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('recipes')
        return self._request('POST', url, data=kw, params=params)

    def get(self, recipe_id, **kw):
        """
        Get a tag
        """
        url = self._format_url('recipes', recipe_id)
        return self._request('GET', url, data=kw, params=kw)

    def update(self, recipe_id, **kw):
        """
        Update a tag
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('recipes', recipe_id)
        return self._request('PUT', url, data=kw, params=params)

    def delete(self, recipe_id, **kw):
        """
        Delete a tag
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('recipes', recipe_id)
        return self._request('DELETE', url, params=kw)

    def cook(self, recipe_id, **kw):
        """
        Cook a recipe.
        """
        url = self._format_url('recipes', recipe_id, 'cook')
        return self._request('GET', url, params=kw)


class Events(BaseClient):

    def search(self, **kw):
        """
        Search events.
        """
        url = self._format_url('events')
        return self._request('GET', url, params=kw)

    def create(self, **kw):
        kw, params = self._split_auth_params_from_data(
            kw, kw_incl=['must_link'])
        url = self._format_url('events')
        return self._request('POST', url, params=params, data=kw)

    def bulk_create(self, data, **kw):
        """
        Bulk create events.
        """
        kw, params = self._split_auth_params_from_data(
            kw, kw_incl=['must_link'])
        url = self._format_url('events', 'bulk')
        return self._request('POST', url, params=params, data=data)

    def get(self, event_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id)
        return self._request('GET', url, params=kw)

    def update(self, event_id, **kw):
        """
        Get an individual event.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('events', event_id)
        return self._request('PUT', url, data=kw, params=params)

    def delete(self, event_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id)
        return self._request('DELETE', url, params=kw)

    def add_tag(self, event_id, tag_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id, 'tags', tag_id)
        return self._request('PUT', url, params=kw)

    def remove_tag(self, event_id, tag_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id, 'tags', tag_id)
        return self._request('DELETE', url, params=kw)

    def add_content_item(self, event_id, content_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id, 'content', content_id)
        return self._request('PUT', url, params=kw)

    def remove_content_item(self, event_id, content_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id, 'content', content_id)
        return self._request('DELETE', url, params=kw)


class Content(BaseClient):

    def search(self, **kw):
        """
        search all content items.
        """
        url = self._format_url('content')
        return self._request('GET', url, params=kw)

    def get(self, content_id, **kw):
        """
        Get an individual content item.
        """
        url = self._format_url('content', content_id)
        return self._request('GET', url, params=kw)

    def create(self, **kw):
        """
        Create a content item.
        """
        kw, params = self._split_auth_params_from_data(kw, kw_incl=['extract'])
        url = self._format_url('content')
        return self._request('POST', url, params=params, data=kw)

    def bulk_create(self, data, **kw):
        """
        Bulk create content items.
        """
        kw, params = self._split_auth_params_from_data(kw, kw_incl=['extract'])
        url = self._format_url('content', 'bulk')
        return self._request('POST', url, params=params, data=data)

    def update(self, content_id, **kw):
        """
        Update a content item.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('content', content_id)
        return self._request('PUT', url, params=params, data=kw)

    def delete(self, content_id, **kw):
        """
        Delete a content item.
        """
        url = self._format_url('content', content_id)
        return self._request('DELETE', url, params=kw)

    def get_timeseries(self, content_id, **kw):
        """
        Get a content item timeseries.
        """
        url = self._format_url('content', content_id, 'timeseries')
        return self._request('GET', url, params=kw)

    def create_timeseries(self, content_id, **kw):
        """
        Create timeseries metric(s) for a content item.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('content', content_id, 'timeseries')
        return self._request('POST', url, params=params, data=kw)

    def bulk_create_timeseries(self, data, **kw):
        """
        Bulk create timeseries metric(s) for content items.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('content', 'timeseries', 'bulk')
        return self._request('POST', url, params=params, data=data)

    def get_summary(self, content_id, **kw):
        """
        Get a content item timeseries.
        """
        url = self._format_url('content', content_id, 'summary')
        return self._request('GET', url, params=kw)

    def create_summary(self, content_id, **kw):
        """
        Create summary metric(s) for a content item.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('content', content_id, 'summary')
        return self._request('POST', url, params=params, data=kw)

    def bulk_create_summary(self, data, **kw):
        """
        Bulk create summary metric(s) for content items.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('content', 'summary', 'bulk')
        return self._request('POST', url, params=params, data=data)

    def add_tag(self, content_id, tag_id, **kw):
        """
        Tag a content item.
        """
        url = self._format_url('content', content_id, 'tags', tag_id)
        return self._request('PUT', url, params=kw)

    def remove_tag(self, content_id, tag_id, **kw):
        """
        Remove a tag from a content item.
        """
        url = self._format_url('content', content_id, 'tags', tag_id)
        return self._request('DELETE', url, params=kw)


class Extract(BaseClient):

    def get(self, **kw):
        """
        Extract metadata from urls.
        """
        url = self._format_url('extract')
        return self._request('GET', url, params=kw)


class Authors(BaseClient):

    def list(self, **kw):
        """
        List all authors
        """
        url = self._format_url('authors')
        return self._request('GET', url, params=kw)

    def create(self, **kw):
        """
        Create an author.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('authors')
        return self._request('POST', url, params=params, data=kw)

    def get(self, author_id, **kw):
        """
        Get an individual author.
        """
        url = self._format_url('authors', author_id)
        return self._request('GET', url, params=kw)

    def update(self, author_id, **kw):
        """
        Update an author.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('authors', author_id)
        return self._request('PUT', url, data=kw, params=params)

    def delete(self, author_id, **kw):
        """
        Delete an author.
        """
        url = self._format_url('authors', author_id)
        return self._request('DELETE', url, params=kw)

    def add_content_item(self, author_id, content_id, **kw):
        """
        Add an author to a content item.
        """
        url = self._format_url('authors', author_id, 'content', content_id)
        return self._request('PUT', url, params=kw)

    def remove_content_item(self, author_id, content_id, **kw):
        """
        Remove an author from a content item.
        """
        url = self._format_url('authors', author_id, 'content', content_id)
        return self._request('DELETE', url, params=kw)

    def merge(self, from_author_id, to_author_id, **kw):
        """
        Remove an author from a content item.
        """
        url = self._format_url(
            'authors', from_author_id, 'merge', to_author_id)
        return self._request('PUT', url, params=kw)


class Metrics(BaseClient):

    def list(self, **kw):
        """
        List all metrics + faceted counts.
        """
        url = self._format_url('metrics')
        return self._request('GET', url, params=kw)

    def get(self, metric_id, **kw):
        """
        Get an individual metric
        """
        url = self._format_url('metrics', metric_id)
        return self._request('GET', url, params=kw)

    def update(self, metric_id, **kw):
        """
        Update a metric.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('metrics', metric_id)
        return self._request('PUT', url, data=kw, params=params)

    def delete(self, metric_id, **kw):
        """
        Delete a metric and all instances it has been collected.
        """
        url = self._format_url('metrics', metric_id)
        return self._request('DELETE', url, params=kw)


class SQL(BaseClient):

    def execute(self, query, **kw):
        """
        Execute a sql command and stream resutls.
        """
        # merge in api key
        kw.update({'apikey': self.apikey})
        url = self._format_url('sql')

        # post request
        r = requests.post(url, params=kw, data={'query': query})

        # stream results.
        for line in r.iter_lines():
            d = json_to_obj(line)

            # catch errors
            if d.get('error'):
                err = ERRORS.get(d['error'])
                if not err:
                    raise ClientError(d)
                raise err(d['message'])
            yield d


class Jobs(BaseClient):

    def get_status(self, **kw):
        """
        Get a job's status.
        """
        status_url = kw.get('status_url')
        if not status_url:
            raise ClientError(
                'You must pass in the "status_url" returned from a bulk/recipe endpoint.')
        r = requests.get(status_url)
        d = r.json()
        # catch errors
        if d.get('error'):
            err = ERRORS.get(d['error'])
            if not err:
                raise ClientError(d)
            raise err(d['message'])
        return d

    def poll_status(self, **kw):
        """
        Poll a job's status until it's successful.
        """
        interval = kw.get('interval', 5)
        while True:
            d = self.get_status(**kw)
            print d
            if not d.get('status'):
                continue

            if d.get('status') == 'success':
                return True

            elif d.get('status') == 'error':
                raise JobError(d.get('message', ''))

            else:
                time.sleep(interval)


class SousChefs(BaseClient):

    def list(self, **kw):
        """
        Get all sous chefs / facets.
        """
        url = self._format_url('sous-chefs')
        return self._request('GET', url, params=kw)

    def create(self, **kw):
        """
        Create a sous chef.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('sous-chefs')
        return self._request('POST', url, data=kw, params=params)

    def get(self, sous_chef_id, **kw):
        """
        Get a sous chef.
        """
        url = self._format_url('sous-chefs', sous_chef_id)
        return self._request('GET', url, data=kw, params=kw)

    def update(self, sous_chef_id, **kw):
        """
        Update a sous chef.
        """
        kw, params = self._split_auth_params_from_data(kw)
        url = self._format_url('sous-chefs', sous_chef_id)
        return self._request('PUT', url, data=kw, params=params)


# TODO:
class Reports(BaseClient):
    pass


class API(BaseClient):

    """
    A class for interacting with the TenderEngine API.
    """

    def __init__(self, **kw):
        BaseClient.__init__(self, **kw)
        self.me = Me(**kw)
        self.orgs = Orgs(**kw)
        self.settings = Settings(**kw)
        self.tags = Tags(**kw)
        self.sous_chefs = SousChefs(**kw)
        self.recipes = Recipes(**kw)
        self.events = Events(**kw)
        self.content = Content(**kw)
        self.metrics = Metrics(**kw)
        self.reports = Reports(**kw)
        self.authors = Authors(**kw)
        self.extract = Extract(**kw)
        self.sql = SQL(**kw)
        self.jobs = Jobs(**kw)
