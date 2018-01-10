import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import time, random, os


def generate_message_id(msg_from):
    domain = msg_from.split("@")[1]
    r = "%s.%s" % (time.time(), random.randint(0, 100))
    mid = "<%s@%s>" % (r, domain)
    return mid


class Gmail(object):
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.server = 'smtp.gmail.com'
        self.port = 587
        session = smtplib.SMTP(self.server, self.port)        
        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(self.email, self.password)
        self.session = session

    def send_message(self, subject, body, files=[]):
        ''' This must be removed '''

        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = COMMASPACE.join(["cj@@xpms.io"])
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        text = body.encode("utf-8")
        text = MIMEText(text, 'plain', "utf-8")
        msg.attach(text)

        msg.add_header('Message-ID', generate_message_id(self.email))

        for file in files:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(file,"rb").read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"'
                           % os.path.basename(file))
            msg.attach(part)

	
        self.session.sendmail(self.email, "cj@xpms.io", msg.as_string())

    def send_message_html(self, to_email_id, subject, body_html, files=[]):
        ''' This must be removed '''

        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = COMMASPACE.join([ to_email_id ])
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        text = body_html.encode("utf-8")
        text = MIMEText(text, 'html', "utf-8")
        msg.attach(text)

        msg.add_header('Message-ID', generate_message_id(self.email))

        for file in files:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(file,"rb").read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"'
                           % os.path.basename(file))
            msg.attach(part)

	
        self.session.sendmail(self.email, to_email_id, msg.as_string())



#gm = Gmail('info@reelsandframes.in', 'sk8erboI!m')
# #gm.send_message('Subject', 'Message', ["DAY02_02_RNF_YK_WELCOME_DINNER-1293.jpg"])
#html_code = """ <img src=https://s3-eu-west-1.amazonaws.com/testset1/bro.jpg>  <img src=https://s3-eu-west-1.amazonaws.com/testset1/bro.jpg> <img src=https://s3-eu-west-1.amazonaws.com/testset1/bro.jpg> """
#gm.send_message_html('chetan.j9@gmail.com','Found few photos of you!', html_code)
#
