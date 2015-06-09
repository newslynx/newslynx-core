from flask import Blueprint

from newslynx.models import Auth
from newslynx.lib.serialize import jsonify
from newslynx.views.decorators import load_user, load_org

# blueprint
bp = Blueprint('all_auth', __name__)


# GOOGLE ANALYTICS OAUTH ENDPOINTS #
@bp.route('/api/v1/auths', methods=['GET'])
@load_user
@load_org
def get_all_auths(user, org):
    """
    Get all authorizations for an org.
    """
    tokens = Auth.query\
        .filter_by(org_id=org.id)\
        .all()
    return jsonify(tokens)
