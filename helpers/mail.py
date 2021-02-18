"""Mail helper."""

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

def send_gmail(send_from, pwd, send_to, subject, text, attachments=None):
    """
    Send E-Mail using GMail

    @param string send_from
    @param string pwd
    @param list send_to
    @param string subject
    @param string text
    @param list files (optional)
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text, 'html'))

    for attachment in attachments or []:
        with open(attachment, 'rb') as fil:
            part = MIMEApplication(fil.read(), Name=os.path.basename(attachment))

        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(attachment)
        msg.attach(part)

    try:
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(send_from, pwd)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()
    except Exception:
        print('Failed to send mail')
