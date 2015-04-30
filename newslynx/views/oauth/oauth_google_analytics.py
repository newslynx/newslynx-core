from urlparse import urljoin

from flask import (
    Blueprint, request, session, redirect
)

## TODO: remove reliance on this library for oauth
import googleanalytics
from googleanalytics.auth import Credentials

from newslynx import settings
from newslynx.core import db
from newslynx.models import Auth
from newslynx.exc import AuthError, RequestError
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import obj_or_404, delete_response

# blueprint
bp = Blueprint('oauth_google_analytics', __name__)

# check for necessary credentials
try:
    getattr(settings, 'GOOGLE_ANALYTICS_CLIENT_ID')
    getattr(settings, 'GOOGLE_ANALYTICS_CLIENT_SECRET')
    GA_ENABLED = True
except:
    GA_ENABLED = False

if GA_ENABLED:
    # auth flow #
    ga_oauth = googleanalytics.auth.Flow(
        settings.GOOGLE_ANALYTICS_CLIENT_ID,
        settings.GOOGLE_ANALYTICS_CLIENT_SECRET,
        redirect_uri=urljoin(settings.API_URL,
                             '/api/v1/auth/google-analytics/callback'))


# oauth utilities #


def ga_revoke_access(tokens):
    """
    Revoke a google analytics token.
    """
    tokens['client_id'] = settings.GOOGLE_ANALYTICS_CLIENT_ID
    tokens['client_secret'] = settings.GOOGLE_ANALYTICS_CLIENT_ID
    creds = Credentials(**tokens)
    creds.revoke()


def ga_properties(tokens):
    """
    Get a list of properties associated with a google analytics account.
    """
    accounts = googleanalytics.authenticate(**tokens)
    properties = []
    for account in accounts:
        for prop in account.webproperties:
            website_url = prop.url
            if website_url:
                property = {'web_property': website_url, 'profiles': []}
                for profile in prop.profiles:
                    property['profiles'].append(profile.name)
                properties.append(property)
    return properties


# GOOGLE ANALYTICS OAUTH ENDPOINTS #
@bp.route('/api/v1/auth/google-analytics', methods=['GET'])
@load_user
@load_org
def ga_auth(user, org):

    # raise error when configurations are not provided.
    if not GA_ENABLED:
        raise AuthError(
            'You must provide a "google_analytics_client_id" and '
            '"google_analytics_client_secret in your '
            'NewsLynx configuration to enable Twitter integration. '
            'See https://developers.google.com/analytics/ for details on how to create '
            'an application on Google Analytics.')

    # Get Auth Url
    authorize_url = ga_oauth.step1_get_authorize_url()

    # store the user / apikey in the session:
    session['org_id'] = org.id
    session['redirect_uri'] = request.args.get('redirect_uri')

    # Send the user to the auth URL.
    return redirect(authorize_url)


# callback
@bp.route('/api/v1/auth/google-analytics/callback')
def ga_callback():

    # pop session
    org_id = session.pop('org_id')
    redirect_uri = session.pop('redirect_uri')

    # get tokens
    tokens = ga_oauth.step2_exchange(request.args['code']).serialize()

    # if we got a refresh token, store it.
    # Otherwise it means the user is already authenticated
    if 'refresh_token' not in tokens or not tokens['refresh_token']:
        # TK: Figure out how to notify APP that user is already registered?
        raise RequestError(
            "You've already authenticated with google-analytics!")

    # fetch properties
    tokens['properties'] = ga_properties(tokens)

    # remove client_id and client_secret
    tokens.pop('client_secret')
    tokens.pop('client_id')

    # upsert Auths
    ga_token = Auth.query\
        .filter_by(name='google_analytics', organization_id=org_id)\
        .first()

    if not ga_token:

        # create settings object
        ga_token = Auth(
            organization_id=org_id,
            name='google_analytics',
            value=tokens)

    else:
        ga_token.value = tokens

    db.session.add(ga_token)
    db.session.commit()

    # redirect to app
    if redirect_uri:
        return redirect(redirect_uri)

    return jsonify(ga_token)


@bp.route('/api/v1/auth/google-analytics/revoke', methods=['GET'])
@load_user
@load_org
def ga_revoke(user, org):

    ga_token = Auth.query\
        .filter_by(organization_id=org.id, name='google_analytics')\
        .first()

    obj_or_404(ga_token,
               'You have not authenticated yet with google-analytics.')

    token = ga_token.to_dict()['value']
    token.pop('properties')

    # revoke google analytics
    ga_revoke_access(token)

    # drop token from table
    db.session.delete(ga_token)
    db.session.commit()

    # redirect to app
    redirect_uri = request.args.get('redirect_uri')
    if redirect_uri:
        return redirect(redirect_uri)

    return delete_response()
