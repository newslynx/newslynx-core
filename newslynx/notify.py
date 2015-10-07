import requests

from newslynx.core import settings
from newslynx.lib.serialize import obj_to_json
from newslynx.lib.mail import Server
from newslynx.lib import dates


class Notification(object):

    """
    An abstract notification class.
    """

    def format(self, tb, **kw):
        return tb

    def dispatch(self, msg):
        raise NotImplemented('Must implement a dispatch method')

    def send(self, tb, **kw):
        return self.dispatch(self.format(tb, **kw), **kw)


class EmailNotificaton(Notification):

    server = Server()

    def dispatch(self, msg, **kw):
        self.server.outbox.login()
        kw = {
            'subject': "{} <{}> {}".format(
                settings.NOTIFY_EMAIL_SUBJECT_PREFIX,
                kw.get('subject', 'none'),
                dates.now().isoformat()),
            'body': msg,
            'to_': kw.get('to_', ",".join(settings.NOTIFY_EMAIL_RECIPIENTS)),
            'from_':  kw.get('from_', settings.MAIL_USERNAME)
        }
        self.server.outbox.send(**kw)
        self.server.outbox.logout()


class SlackNotification(Notification):

    def dispatch(self, msg, **kw):

        payload = {
            "text": msg,
            "channel": kw.get('channel', settings.NOTIFY_SLACK_CHANNEL),
            "username": kw.get('username', settings.NOTIFY_SLACK_USERNAME),
            "icon_emoji": kw.get('icon_emoji', settings.NOTIFY_SLACK_EMOJI)
        }
        requests.post(settings.NOTIFY_SLACK_WEBHOOK, data=obj_to_json(payload))

# lookup of config param to notification engine.
METHODS = {
    'slack': SlackNotification(),
    'email': EmailNotificaton()
}
