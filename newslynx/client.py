import os
import copy

from requests import Session, Request
from addict import Dict
from urlparse import urljoin

from newslynx import settings
from newslynx.lib.serialize import obj_to_json
from newslynx.exc import ClientError

RET_CODES = [200, 201]
GOOD_CODES = RET_CODES + [204]


class API(object):

    """
    A class for interacting with the TenderEngine API.
    """

    def __init__(self, **kw):

        # defaults / helpers
        self._url = kw.pop('url', settings.API_URL)

        # standardize url
        if not self._url.endswith('/'):
            self._url += '/'

        self._org = kw.pop('org', None)
        self._version = kw.pop('version', 'v1')
        self._endpoint = self._url + 'api/' + self._version + "/"

        # establish session
        self._session = Session()

        # authenticate
        self._auth(**kw)

    def login(self, **kw):
        """
        Authenticate with newslynx.
        """

        url = self._format_url('login')
        return self._request('POST', url, data=kw)

    def me(self, **kw):
        """
        Fetch your user profile.
        """

        url = self._format_url('me')
        return self._request('GET', url, params=kw)

    def me_update(self, **kw):
        """
        Update your user profile.
        """
        kw, params = self._split_auth_params_from_kw(**kw)
        url = self._format_url('me')
        return self._request('PUT', url, data=kw, params=kw)

    def me_orgs(self, **kw):
        """
        Get orgs you have access to.
        """
        url = self._format_url('orgs')
        return self._request('GET', url, params=kw)

    def org(self, org=None, **kw):
        """
        Get an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        url = self._format_url('orgs', org)
        return self._request('GET', url, params=kw)

    def org_create(self, **kw):
        """
        Create an organization.
        """
        kw, params = self._split_auth_params_from_kw(**kw)
        url = self._format_url('orgs')
        return self._request('POST', url, data=kw, params=params)

    def org_update(self, org=None, **kw):
        """
        Update an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')
        kw, params = self._split_auth_params_from_kw(**kw)
        url = self._format_url('orgs', org)
        return self._request('PUT', url, data=kw, params=params)

    def org_delete(self, org=None, **kw):
        """
        Delete an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        url = self._format_url('orgs', org)
        return self._request('DELETE', url, params=kw)

    def org_create_user(self, org=None, **kw):
        """
        Create a user under an org.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')
        kw, params = self._split_auth_params_from_kw(**kw)
        url = self._format_url('orgs', org, 'users')
        return self._request('POST', url, data=kw, params=params)

    def org_user(self, org=None, user=None, **kw):
        """
        Get a user profile from an organization
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        elif not user:
            raise ValueError(
                'You must pass in the user id or email as the second argument.')

        url = self._format_url('orgs', org, 'users', user)
        return self._request('GET', url, params=kw)

    def org_users(self, org=None, **kw):
        """
        Get all user profiles under an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        url = self._format_url('orgs', org, 'users')
        return self._request('GET', url, params=kw)

    def org_add_user(self, org=None, user=None, **kw):
        """
        Add an existing user to an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        elif not user:
            raise ValueError(
                'You must pass in the user id or email as the second argument.')

        url = self._format_url('orgs', org, 'users', user)
        return self._request('PUT', url, params=kw)

    def org_remove_user(self, org=None, user=None, **kw):
        """
        Remove an existing user from an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        elif not user:
            raise ValueError(
                'You must pass in the user id or email as the second argument.')

        url = self._format_url('orgs', org, 'users', user)
        return self._request('DELETE', url, params=kw)

    def org_add_setting(self, org=None, **kw):
        """
        Add/update a setting for an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        # jsonify value
        if kw.get('json_value', True):
            if not isinstance(kw.get('value'), basestring):
                kw['value'] = obj_to_json(kw['value'])

        kw, params = self._split_auth_params_from_kw(**kw)

        url = self._format_url('orgs', org, 'settings')
        return self._request('POST', url, data=kw, params=params)

    def org_delete_setting(self, org=None, name=None, **kw):
        """
        Add/update a setting for an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        elif not name:
            raise ValueError(
                'You must pass in the user id or email as the second argument.')

        url = self._format_url('orgs', org, 'settings', name)
        return self._request('DELETE', url, params=kw)

    def org_setting(self, org=None, name=None, **kw):
        """
        Add/update a setting for an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        elif not name:
            raise ValueError(
                'You must pass in the user id or email as the second argument.')

        url = self._format_url('orgs', org, 'settings', name)
        return self._request('GET', url, **kw)

    def org_settings(self, org=None, **kw):
        """
        Add/update a setting for an organization.
        """
        if not org:
            org = copy.copy(self._org)
            if not org:
                raise ValueError(
                    'You must pass in the org ID or name as the first argument.')

        url = self._format_url('orgs', org, 'settings')
        return self._request('GET', url, params=kw)

    def events(self, **kw):
        """
        Search events.
        """
        if not kw.get('org'):
            kw['org'] = copy.copy(self._org)
            if not kw['org']:
                raise ValueError(
                    'You must pass in the org ID or name as a keyword argument.')

        url = self._format_url('events')
        return self._request('GET', url, params=kw)

    def event(self, event_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id)
        return self._request('GET', url, params=kw)

    def event_update(self, event_id, **kw):
        """
        Get an individual event.
        """
        kw, params = self._split_auth_params_from_kw(**kw)
        url = self._format_url('events', event_id)
        return self._request('PUT', url, data=kw, params=params)

    def event_delete(self, event_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id)
        return self._request('DELETE', url, params=kw)

    def event_add_tag(self, event_id, tag_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id, 'tags', tag_id)
        return self._request('PUT', url, params=kw)

    def event_delete_tag(self, event_id, tag_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id, 'tags', tag_id)
        return self._request('DELETE', url, params=kw)

    def event_add_thing(self, event_id, thing_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id, 'things', thing_id)
        return self._request('PUT', url, params=kw)

    def event_delete_thing(self, event_id, thing_id, **kw):
        """
        Get an individual event.
        """
        url = self._format_url('events', event_id, 'things', thing_id)
        return self._request('DELETE', url, params=kw)

    def tags(self, **kw):
        """
        Get all tags.
        """
        url = self._format_url('tags')
        return self._request('GET', url, params=kw)

    def tag_update(self, tag_id, **kw):
        """
        Update a tag
        """
        kw, params = self._split_auth_params_from_kw(**kw)
        url = self._format_url('tags', tag_id)
        return self._request('PUT', url, data=kw, params=params)

    def tag_delete(self, tag_id, **kw):
        """
        Delete a tag
        """
        kw, params = self._split_auth_params_from_kw(**kw)
        url = self._format_url('tags', tag_id)
        return self._request('DELETE', url, params=kw)

    def _auth(self, **kw):
        """
        Authenticate on initalization.
        """
        # get key
        self.apikey = kw.get('apikey', os.getenv('NEWSLYNX_API_KEY'))

        # if no key is provided, login.
        if not self.apikey:
            email = kw.get('email', settings.ADMIN_EMAIL)
            password = kw.get('password', settings.ADMIN_PASSWORD)
            resp = self.login(email=email, password=password)
            self.apikey = resp.apikey

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

        # pop internal flags
        apikey = kw.pop('apikey', self.apikey)

        # add params to kw
        kw.setdefault('params', {})

        # add apikey/org when required or set by user.
        if not url.endswith('/login'):
            kw['params'].update({'apikey': apikey})
            if 'org' not in kw['params']:
                kw['params']['org'] = self._org

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

    def _split_auth_params_from_kw(self, **kw):
        params = {}
        if 'apikey' in kw:
            params['apikey'] = kw.pop('apikey')
        if 'org' in kw:
            params['org'] = kw.pop('org')
        return kw, params

    def _handle_errors(self, resp, err=None):
        """
        Handle all errors.
        """
        if err:
            raise err

        # check status codes
        elif resp.status_code not in GOOD_CODES:
            raise ClientError(resp.content)

    def _format_response(self, resp):
        """
        Format a response with addict.Dict
        """

        # if there's no response just return true.
        if resp.status_code not in RET_CODES:
            return True

        data = resp.json()
        if isinstance(data, list):
            return [Dict(d) for d in data]

        return Dict(data)
