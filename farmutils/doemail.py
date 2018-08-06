import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email import encoders

DEFAULT_SMTP = 'smtp.office365.com'
DEFAULT_TIMEOUT = 587


class EmailInvalidSettings(Exception):
    pass


class Email():
    """ Create and send emails """
    def __init__(self):
        self.mail_settings = {}
        self.smtp_settings = {}
        self.attachments = []

    def log(self, message):
        """ Very basic logging function. Should change in future """
        print(message)

    def error(self, message):
        """ Very basic error function. Should change in future """
        self.log('ERROR: {}'.format(message))

    def send(self):
        """ Validate settings, compose message, and send """
        if self._validate():
            msg = self._compose()
            try:
                self._send(msg)
            except smtplib.SMTPException as e:
                self.error(str(e))
                raise(e)
        else:
            self.error("Send failed. Invalid settings.")

    def _send(self, msg):
        """ Send email with current settings """
        with smtplib.SMTP(
                self.smtp_settings['server'],
                self.smtp_settings['timeout']) as smtp:
            smtp.starttls()
            smtp.login(self.mail_settings['from'],
                       self.smtp_settings['password'])
            text = msg.as_string()

            recipients = [self.mail_settings['to']]
            if _has_param(self.mail_settings, 'cc'):
                recipients.append(self.mail_settings['cc'])
            if _has_param(self.mail_settings, 'bcc'):
                recipients.append(self.mail_settings['bcc'])

            smtp.sendmail(self.mail_settings['from'], recipients, text)

    def _compose(self):
        """ Combine saved settings into a MIME multipart message """
        msg = MIMEMultipart('mixed')
        msg.preamble = 'This is a multi-part message in MIME format.'

        msg['To'] = self.mail_settings['to']
        msg['From'] = self.mail_settings['from']
        msg['Subject'] = self.mail_settings['subject']

        msg.attach(MIMEText(self.mail_settings['body'], 'plain'))

        for a in self.attachments:
            msg.attach(a)

        return msg

    def _validate(self):
        """ Check email has all required settings """
        valid = True

        # Check email settings
        if not _has_param(self.mail_settings, 'to'):
            self.error("To address is not set")
            valid = False
        if not _has_param(self.mail_settings, 'from'):
            self.error("From address is not set")
            valid = False

        # Check SMTP settings
        if not _has_param(self.smtp_settings, 'password'):
            self.error("smtp password not set")
            valid = False
        if not _has_param(self.smtp_settings, 'server'):
            self.error("smtp server not set")
            valid = False
        if not _has_param(self.smtp_settings, 'timeout'):
            self.error("smtp timeout not set")
            valid = False

        if not valid:
            raise EmailInvalidSettings

        return valid

    def set_smtp(self, password, server=DEFAULT_SMTP, timeout=DEFAULT_TIMEOUT):
        """ Set SMTP email settings """
        self.smtp_settings['password'] = password
        self.smtp_settings['server'] = server
        self.smtp_settings['timeout'] = timeout

    def set_addr(self, to_addr, from_addr, cc_addr=None, bcc_addr=None):
        """ Set sender and recipents email settings """
        self.mail_settings['from'] = from_addr
        self.mail_settings['to'] = ', '.join(_to_list(to_addr))
        if cc_addr:
            self.mail_settings['cc'] = ', '.join(_to_list(cc_addr))
        if bcc_addr:
            self.mail_settings['bcc'] = ', '.join(_to_list(bcc_addr))

    def set_text(self, subject=None, body=None):
        """ Set subject and body of email """
        self.mail_settings['body'] = body
        self.mail_settings['subject'] = subject

    def set_attachments(self, files=None, images=None):
        """ Attach files and images

        files -- Files are attached as plain attachments.
        images -- Images are attached, & inline HTML inserted.
        """

        # Clear old attachments
        self.attachments = []

        if files:
            for f in _to_list(files):
                # Attach files as attachments
                try:
                    with open(f, 'rb') as fp:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(fp.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', "attachment; filename={}".format(
                        os.path.basename(f)))
                    self.attachments.append(part)
                except IOError:
                    self.error("Could not file for attachment: {}".format(f))

        if images:
            for i in _to_list(images):
                # Attach images inline
                try:
                    ibn = os.path.basename(i)
                    cid = 'image_{}'.format(ibn.replace('.', '_'))
                    with open(i, 'rb') as fp:
                        part = MIMEImage(fp.read(), name=ibn)
                    part.add_header('Content-ID', '<{}>'.format(cid))
                    self.attachments.append(part)
                    self.attachments.append(MIMEText(
                        u'<img src="cid:{}" alt="{}">'.format(cid, ibn), 'html', 'utf-8'))
                except IOError:
                    self.error("Could not image for attachment: {}".format(i))


def _has_param(d, k):
    """ Check whether dict has key, and value is not empty """
    if not d or not k or k not in d or not d[k]:
        return False
    else:
        return True


def _to_list(attr):
    """ Return list version of attr """
    if isinstance(attr, list):
        return attr
    else:
        return [attr]
