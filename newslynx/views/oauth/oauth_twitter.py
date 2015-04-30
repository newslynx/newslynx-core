from flask import (
    Blueprint, request, session, redirect, url_for
)
from rauth.utils import parse_utf8_qsl
from rauth.service import OAuth1Service

from newslynx import settings
from newslynx.core import db
from newslynx.models import Auth
from newslynx.exc import AuthError, RequestError
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org
from newslynx.views.util import obj_or_404, delete_response

# blueprint
bp = Blueprint('oauth_twitter', __name__)

# check for necessary credentials
try:
    getattr(settings, 'TWITTER_API_KEY')
    getattr(settings, 'TWITTER_API_SECRET')
    TWT_ENABLED = True
except:
    TWT_ENABLED = False

# auth flow
if TWT_ENABLED:

    twt_oauth = OAuth1Service(
        name='twitter',
        consumer_key=settings.TWITTER_API_KEY,
        consumer_secret=settings.TWITTER_API_SECRET,
        request_token_url='https://api.twitter.com/oauth/request_token',
        access_token_url='https://api.twitter.com/oauth/access_token',
        authorize_url='https://api.twitter.com/oauth/authorize',
        base_url='https://api.twitter.com/1.1/')


# TWITTER OAUTH ENDPOINTS #
@bp.route('/api/v1/auth/twitter', methods=['GET'])
@load_user
@load_org
def twt_auth(user, org):

    # raise error when configurations are not provided.
    if not TWT_ENABLED:
        raise AuthError(
            'You must provide a "twitter_api_key" and "twitter_api_secret" in '
            'your NewsLynx configuration to enable Twitter integration. '
            'See http://dev.twitter.com for details on how to create '
            'an application on Twitter.')

    # get callback url
    oauth_callback = url_for('oauth_twitter.twt_callback', _external=True)
    params = {'oauth_callback': oauth_callback}

    # make initial authentication request
    r = twt_oauth.get_raw_request_token(params=params)

    # parse out request tokens into the session
    data = parse_utf8_qsl(r.content)

    session['twitter_oauth'] = (
        data['oauth_token'], data['oauth_token_secret'])
    session['org_id'] = org.id
    session['redirect_uri'] = request.args.get('redirect_uri')

    # redirect the user to the auth url.
    return redirect(twt_oauth.get_authorize_url(data['oauth_token'], **params))


@bp.route('/api/v1/auth/twitter/callback')
def twt_callback():

    if 'twitter_oauth' not in session:
        raise RequestError(
            'An unkonwn error occurred during the twitter authentication process.')

    # get the request tokens from the session
    request_token, request_token_secret = session.pop('twitter_oauth')
    org_id = session.pop('org_id')
    redirect_uri = session.pop('redirect_uri')

    # check to make sure the user authorized the request
    if not 'oauth_token' in request.args:
        raise RequestError(
            'An unkonwn error occurred during the twitter authentication process.')

    # get stable authentication tokens
    creds = {
        'request_token': request_token,
        'request_token_secret': request_token_secret
    }
    params = {'oauth_verifier': request.args['oauth_verifier']}
    oauth_token, oauth_token_secret = twt_oauth.get_access_token(
        params=params, **creds)

    # store stable access tokens
    tokens = {
        'oauth_token': oauth_token,
        'oauth_token_secret': oauth_token_secret
    }

    # upsert settings
    twt_token = Auth.query\
        .filter_by(name='twitter', organization_id=org_id)\
        .first()

    if not twt_token:

        # create settings object
        twt_token = Auth(
            organization_id=org_id,
            name='twitter',
            value=tokens)

    else:
        twt_token.value = tokens

    db.session.add(twt_token)
    db.session.commit()

    # redirect to app
    if redirect_uri:
        return redirect(redirect_uri)

    return jsonify(twt_token)


@bp.route('/api/v1/auth/twitter/revoke', methods=['GET'])
@load_user
@load_org
def twt_revoke(user, org):

    twt_token = Auth.query\
        .filter_by(name='twitter', organization_id=org.id)\
        .first()

    obj_or_404(twt_token, 'You have not authenticated yet with Twitter.')

    # drop token from table
    db.session.delete(twt_token)
    db.session.commit()

    # redirect to app
    redirect_uri = request.args.get('redirect_uri')
    if redirect_uri:
        return redirect(redirect_uri)

    return delete_response()
