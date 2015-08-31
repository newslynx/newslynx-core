"""
Sync sous chefs accross all organizations for an install.
"""
import sys
import logging

from newslynx.core import settings
from newslynx.tasks import default
from newslynx.models import User
from newslynx.sc import sc_module

log = logging.getLogger(__name__)


def orgs():
    """
    Sync sous chefs for all Orgs.
    """
    # create the super user and add to the org.
    u = User.query.filter_by(email=settings.SUPER_USER_EMAIL).first()
    if not u:
        log.error('You must initialized NewsLynx before syncing Sous Chefs')
        sys.exit(1)

    log.info('Updating all Sous Chef Modules')
    sc_module.update_all()
    for org in u.orgs:
        log.info('Syncing sous chefs for organization: {}'.format(org.name))
        default.sous_chefs(org)
