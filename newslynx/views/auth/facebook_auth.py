from flask import (
    Blueprint, request, session, redirect, url_for
)
from rauth.utils import parse_utf8_qsl
from rauth.service import OAuth2Service
import requests

from newslynx.core import settings
from newslynx.core import db
from newslynx.models import Auth
from newslynx.exc import AuthError, RequestError
from newslynx.lib.serialize import jsonify
from newslynx.lib import dates
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import obj_or_404, delete_response
from newslynx.lib import url


# blueprint
bp = Blueprint('auth_facebook', __name__)


# auth flow
if settings.FB_ENABLED:
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
    token['expires'] = dates.parse_ts(
        dates.now(ts=True) + int(token['expires'])).isoformat()
    return token


# GOOGLE ANALYTICS OAUTH ENDPOINTS #
@bp.route('/api/v1/auths/facebook', methods=['GET'])
@load_user
@load_org
def get_ga_auth(user, org):
    token = Auth.query\
        .filter_by(org_id=org.id, name='facebook')\
        .first()
    obj_or_404(token,
               'You have not authenticated yet with facebook.')
    return jsonify(token)


@bp.route('/api/v1/auths/facebook/grant', methods=['GET'])
@load_user
@load_org
def fb_auth(user, org):

    # raise error when configurations are not provided.
    if not settings.FB_ENABLED:
        raise RequestError(
            'You must provide a "facebook_app_id" and "facebook_app_secret" in '
            'your NewsLynx configuration to enable facebook integration. '
            'See http://developers.facebook.com for details on how to create '
            'an application on Facebook.')

    oauth_callback = url_for('auth_facebook.fb_callback', _external=True)
    params = {'redirect_uri': oauth_callback}

    # set user creds on session
    session['org_id'] = org.id
    session['redirect_uri'] = request.args.get('redirect_uri')

    return redirect(fb_oauth.get_authorize_url(**params))


@bp.route('/api/v1/auths/facebook/callback')
def fb_callback():

    org_id = session.pop('org_id')
    redirect_uri = session.pop('redirect_uri')

    # check to make sure the user authorized the request
    if not 'code' in request.args:
        if not redirect_uri:
            raise AuthError('You did not authorize the request to facebook.')

        uri = url.add_query_params(redirect_uri, auth_success='false')
        return redirect(uri)

    # make a request for the access token credentials using code
    authorize_uri = url_for('auth_facebook.fb_callback', _external=True)
    data = dict(code=request.args['code'], redirect_uri=authorize_uri)

    # get a temporary access token
    temp_access_token = fb_oauth.get_access_token(data=data)
    tokens = fb_extend_oauth_token(temp_access_token)

    # upsert settings
    facebook_token = Auth.query\
        .filter_by(name='facebook', org_id=org_id)\
        .first()

    if not facebook_token:

        # create settings object
        facebook_token = Auth(
            org_id=org_id,
            name='facebook',
            value=tokens)

    else:
        facebook_token.value = tokens

    db.session.add(facebook_token)
    db.session.commit()

    if redirect_uri:
        uri = url.add_query_params(redirect_uri, auth_success='true')
        return redirect(uri)

    return jsonify(facebook_token)


@bp.route('/api/v1/auths/facebook/revoke', methods=['GET'])
@load_user
@load_org
def fb_revoke(user, org):

    fb_token = Auth.query\
        .filter_by(name='facebook', org_id=org.id)\
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
