"""
All things related to sending + recieving of emails.
"""

# email imports
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

# newslynx
from newslynx.core import settings
from newslynx.lib.pkg.validate_email import validate_email
from newslynx.lib import dates


def validate(address):
    """
    Validates an email address via regex.
    """
    return validate_email(address, check_mx=False, verify=False)


class Inbox(object):

    """
    A class for interacting with an email inbox.
    """

    def __init__(self, **kw):

        self.username = kw.get('username', settings.MAIL_USERNAME)
        self.password = kw.get('password', settings.MAIL_PASSWORD)
        self.server = kw.get('server', settings.MAIL_SERVER)
        self.port = kw.get('port', settings.MAIL_IMAP_PORT)

    def fetch(self, id):
        """
        Fetch and validate email message by ID.
        """
        result, msg = self.connection.fetch(id, "(RFC822)")
        raw = msg[0][1]
        return self._parse(raw)

    def search(self, subject=None):
        """
        check inbox.
        """
        self.login()
        q = self._gen_query(subject)
        result, data = self.connection.search(None, q)
        ids = data[0]
        id_list = ids.split()
        if len(id_list):
            for id in id_list:
                yield self.fetch(id)
        else:
            yield None
        self.logout()

    def login(self):
        """
        Login to check new mail.
        """
        self.connection = imaplib.IMAP4_SSL(self.server)
        self.connection.login(self.username, self.password)
        self.connection.select('inbox')

    def logout(self):
        """
        Logout to refresh.
        """
        self.connection.logout()

    def _gen_query(self, subject=None):
        """
        Format the query from the subject.
        """
        if not subject:
            return "ALL"
        else:
            return '(SUBJECT "{}")'.format(subject)

    def _parse(self, raw):
        """
        pre process raw message
        """
        # validate the message
        msg = email.message_from_string(raw)
        # normalize
        clean = {}
        rec_parts = msg['Received'].split(';')
        if len(rec_parts) > 1:
            clean['datetime'] = dates.parse_any(rec_parts[-1].strip())
        else:
            clean['datetime'] = dates.now()
        clean['from'] = msg['from'].replace('<', '').replace('>', '')
        clean['to'] = msg['to'].replace('<', '').replace('>', '').strip()
        clean['subject'] = msg['subject'].strip()
        clean['body'] = msg.as_string()
        # return
        return clean


class Outbox(object):

    def __init__(self, **kw):
        """
        Initialize outbox connection.
        """
        self.username = kw.get('username', settings.MAIL_USERNAME)
        self.password = kw.get('password', settings.MAIL_PASSWORD)
        self.server = kw.get('server', settings.MAIL_SERVER)
        self.port = kw.get('port', settings.MAIL_SMTP_PORT)

    def login(self):
        """
        Login to of smtp server
        """
        self.connection = SMTP(self.server, self.port)
        self.connection.ehlo()
        self.connection.starttls()
        self.connection.ehlo()
        self.connection.login(self.username, self.password)

    def logout(self):
        """
        Logout of smtp server
        """
        self.connection.close()

    def send(self, **kw):
        """
        Send a message.
        """

        # format message
        message = self._parse(**kw)
        to = [message.get('To')]
        if message.get('Cc') != '':
            to += message.email['Cc'].split(',')

        # send
        ret = self.connection.sendmail(
            message.get('From'),
            to,
            message.as_string())

        # return
        return ret

    def _parse(self, **kw):
        """
        Format an outgoing email.
        """
        email = MIMEMultipart()
        # meta
        email['From'] = kw.get('from_')
        email['To'] = kw.get('to_')
        email['Subject'] = kw.get('subject', '')
        email['Cc'] = kw.get('cc', '')

        # body
        text = MIMEText(
            kw.get('body'),
            kw.get('message_type', 'plain'),
            kw.get('message_encoding', 'us-ascii')
        )
        email.attach(text)
        return email


class Server(object):
    """
    unified wrapper.
    """
    def __init__(self, **kw):
        self.inbox = Inbox(**kw)
        self.outbox = Outbox(**kw)
