from flask import (
    Blueprint, request, session, redirect, url_for
)
from rauth.utils import parse_utf8_qsl
from rauth.service import OAuth2Service
import requests

from newslynx import settings
from newslynx.core import db
from newslynx.models import Auth
from newslynx.exc import AuthError, RequestError
from newslynx.lib.serialize import jsonify
from newslynx.lib import dates
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import obj_or_404, delete_response

# blueprint
bp = Blueprint('oauth_facebook', __name__)

# check for necessary credentials
try:
    getattr(settings, 'FACEBOOK_APP_ID')
    getattr(settings, 'FACEBOOK_APP_SECRET')
    FB_ENABLED = True
except:
    FB_ENABLED = False

# auth flow
if FB_ENABLED:
    _graph_url = 'https://graph.facebook.com/'
    fb_oauth = OAuth2Service(name='facebook',
                             authorize_url='https://www.facebook.com/dialog/oauth',
                             access_token_url=_graph_url + 'oauth/access_token',
                             client_id=settings.FACEBOOK_APP_ID,
                             client_secret=settings.FACEBOOK_APP_SECRET,
                             base_url=_graph_url)


# oauth utilities #

def fb_extend_oauth_token(temp_access_token):
    url = _graph_url + "oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'fb_exchange_token': temp_access_token
    }
    r = requests.get(url=url, params=params)
    token = parse_utf8_qsl(r.content)
    token['expires'] = dates.ts(
        dates.now(ts=True) + int(token['expires'])).isoformat()
    return token


@bp.route('/api/v1/auth/facebook', methods=['GET'])
@load_user
@load_org
def fb_auth(user, org):

    # raise error when configurations are not provided.
    if not FB_ENABLED:
        raise RequestError(
            'You must provide a "facebook_app_id" and "facebook_app_secret" in '
            'your NewsLynx configuration to enabled facebook integration. '
            'See http://developers.facebook.com for details on how to create '
            'an application on Facebook.')

    oauth_callback = url_for('oauth_facebook.fb_callback', _external=True)
    params = {'redirect_uri': oauth_callback}

    # set user creds on session
    session['org_id'] = org.id
    session['redirect_uri'] = request.args.get('redirect_uri')

    return redirect(fb_oauth.get_authorize_url(**params))


@bp.route('/api/v1/auth/facebook/callback')
def fb_callback():
    # check to make sure the user authorized the request
    if not 'code' in request.args:
        raise AuthError('You did not authorize the request to facebook.')

    org_id = session.pop('org_id')
    redirect_uri = session.pop('redirect_uri')

    # make a request for the access token credentials using code
    authorize_uri = url_for('auth.fb_callback', _external=True)
    data = dict(code=request.args['code'], redirect_uri=authorize_uri)

    # get a temporary access token
    temp_access_token = fb_oauth.get_access_token(data=data)
    tokens = fb_extend_oauth_token(temp_access_token)

    # upsert settings
    facebook_settings = Auth.query\
        .filter_by(name='facebook', organization_id=org_id)\
        .first()

    if not facebook_settings:

        # create settings object
        facebook_settings = Auth(
            organization_id=org_id,
            name='facebook',
            value=tokens)

    else:
        facebook_settings.value = tokens

    db.session.add(facebook_settings)
    db.session.commit()

    if redirect_uri:
        return redirect(redirect_uri)

    return jsonify(facebook_settings)


@bp.route('/api/v1/auth/facebook/revoke', methods=['GET'])
@load_user
@load_org
def fb_revoke(user, org):

    fb_token = Auth.query\
        .filter_by(name='facebook', organization_id=org.id)\
        .first()

    obj_or_404(fb_token, 'You have not authenticated yet with Facebook.')

    # drop token from table
    db.session.delete(fb_token)
    db.session.commit()

    # redirect to app
    redirect_uri = request.args.get('redirect_uri')
    if redirect_uri:
        return redirect(redirect_uri)

    return delete_response()
