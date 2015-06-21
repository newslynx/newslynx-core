import logging

from flask import Blueprint, request

from newslynx.views.decorators import load_user
from newslynx.lib.serialize import jsonify
from newslynx.lib import dates
from newslynx.exc import RequestError
from newslynx.core import queues

# blueprint
bp = Blueprint('jobs', __name__)

log = logging.getLogger(__name__)


@bp.route('/api/v1/jobs/<job_id>', methods=['GET'])
@load_user
def get_status(user, job_id):
    """
    Get the status of a queued job.
    """
    queue = request.args.get('queue')
    if not queue:
        raise RequestError(
            'You must pass in the queue name to fetch a job\'s status')

    q = queues.get(queue)
    job = q.fetch_job(job_id)
    if not job:
        raise RequestError(
            'A job with ID {} does not exist'
            .format(job_id))

    # format return value
    ret = {
        'job_id': job_id,
        'queue': queue,
        'datetime': dates.now()
    }

    if job.is_queued:
        ret['status'] = 'queued'

    if job.is_started:
        ret['status'] = 'running'

    if job.is_failed:
        ret['status'] = 'error'

    if job.is_finished:

        rv = job.return_value
        if rv is True:
            ret['status'] = 'success'

        else:
            ret['status'] = 'error'
            ret['message'] = rv.message

    return jsonify(ret)
