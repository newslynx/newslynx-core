import logging

from flask import Blueprint, request, session

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

    # parse args.
    queue = request.args.get('queue')
    if not queue:
        raise RequestError(
            'You must pass in the queue name to fetch a job\'s status')

    if not queue in queues:
        raise RequestError(
            '"{}" is not a valid queue.'
            .format(queue))

    q = queues.get(queue)
    job = q.fetch_job(job_id)
    if not job:
        raise RequestError(
            'A job with ID {} does not exist'
            .format(job_id))

    # fetch metadata about this job
    # from the session
    # parse args.
    started = request.args.get('started')
    orig_url = request.args.get('orig_url')

    if started:
        started = dates.parse_iso(started)

    # format return value
    ret = {
        'job_id': job_id,
        'queue': queue,
        'status': None,
        'started': started,
        'orig_url': orig_url
    }

    # determine time since start
    if started:
        ret['time_since_start'] = (dates.now() - started).seconds

    # determine status
    if job.is_queued:
        ret['status'] = 'queued'

    if job.is_started:
        ret['status'] = 'running'

    if job.is_failed:
        ret['status'] = 'error'
        ret['message'] = "An unknown error occurred."

    if job.is_finished:
        rv = job.return_value

        # job will return true if successful
        if rv is True:
            ret['status'] = 'success'

        # job will return an error if unsuccessful
        else:
            ret['status'] = 'error'
            ret['message'] = str(rv.message)

    return jsonify(ret)
