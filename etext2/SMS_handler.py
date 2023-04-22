import logging, imaplib, smtplib, email, time, ssl, re, os
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from etext2.Message import Message
from datetime import datetime
from etext2.errors import *
from email import encoders
import json

from fast_mail_parser import parse_email

with open("etext2/providers.json") as file:
  PROVIDERS = json.load(file)
with open("etext2/reverse_mimetypes.json") as file:
  reverse_mimetypes = json.load(file)


def get_time():
  return datetime.now().strftime("%m/%d/%y %H:%M:%S")


pattern_uid = re.compile(r'\d+ \(UID (?P<uid>\d+)\)')
text_numbers = [
  'sms.myboostmobile.com', 'text.republicwireless.com', 'mms.att.net',
  'msg.fi.google.com', 'vmpix.com', 'tmomail.net', 'mailmymobile.net',
  'txt.att.net', 'cspire1.com', 'message.ting.com', 'pm.sprint.com',
  'myboostmobile.com', 'mymetropcs.com', 'sms.cricketwireless.net',
  'mms.uscc.net', 'vtext.com', 'mypixmessages.com', 'vmobl.com',
  'mms.cricketwireless.net', 'messaging.sprintpcs.com', 'mmst5.tracfone.com',
  'email.uscc.net', 'vzwpix.com'
]


class EmailHandler:

  def __init__(self, email_, password, loglevel=logging.NOTSET):
    logging.basicConfig(format="%(name)s:%(levelname)s:%(message)s")
    self.logger = logging.getLogger("EmailHandler")
    self.logger.setLevel(loglevel)
    # clear the log file
    with open("etext2/log.log", "w") as file:
      file.write("")
    file_handler = logging.FileHandler("etext2/log.log")
    self.logger.addHandler(file_handler)
    # format: %(asctime)s:%(levelname)s:%(message)s

    self._on_message = None

    self.email_ = email_
    self.password = password

    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(email_, password)
    imap.select(mailbox='inbox', readonly=False)
    self.imap = imap

    email_sender = smtplib.SMTP("smtp.gmail.com")
    email_sender.starttls(context=ssl.create_default_context())
    email_sender.login(email_, password)
    self.email_sender = email_sender

    self.create_texts_folder()

    self.logger.info("Logged in")

  def create_texts_folder(self):
    self.imap.create("texts")

  def move_texts(self):
    for text in self.find_old_texts():
      self.move_email(text, "texts")

  def get_data(self, email_id):
    try:
      status, data = self.imap.fetch(email_id, "(RFC822)")
      if status == "OK":
        message = parse_email(data[0][1])
        headers = message.headers
        sender_email = headers["From"]
        phone_number = re.findall("\\d+", sender_email)
        date = message.date
        try:
          date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S +0000")
        except:
          try:
            date = " ".join([tmp for tmp in date.split()[:-2]])
            date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S")
          except:
            date = None
        data = {
          "id": email_id,
          "subject": message.subject,
          "date_sent": date,
          "sender": sender_email,
        }
        try:
          data["number"] = phone_number[0]
        except:
          data["number"] = ""
        try:
          data["body"] = message.text_plain[0]
        except:
          data["body"] = ""
        try:
          data["html"] = message.text_html[0]
        except:
          data["html"] = ""
        attachments = []
        for attachment in message.attachments:
          try:
            if attachment.content.decode("ascii") != data[
                "body"] and attachment.content.decode("ascii") != "":
              attachments.append(attachment)
          except:
            attachments.append(attachment)
        data["attachments"] = attachments
        # return data
        return Message(self.imap, data)
      else:
        raise StatusNotOKException("get_data()")
    except:
      raise EmailNotFoundException(email_id)

  def move_email(self, email_, destination_label):
    """
    Moves an email to a destination label

    Params:\n
    email -- object of the Message class
    destination_label -- Label to move the folder under
    """
    try:
      email_.body = email_.body.strip()
      imap = self.imap
      resp, items = imap.search(None, 'All')
      if resp == "OK":
        mail_ids = []
        for block in items:
          mail_ids += block.split()

        resp, data = imap.fetch(email_.id, "(UID)")
        msg_uid = pattern_uid.match(str(data[0], 'utf-8')).group("uid")

        result = imap.uid('COPY', msg_uid, destination_label)

        if result[0] == 'OK':
          mov, data = imap.uid('STORE', msg_uid, '+FLAGS', '(\Deleted)')
          imap.expunge()
        self.logger.info("Successfully moved email with ID %s" % email_.id)
        return True, "Moved email successfully"
      else:
        raise StatusNotOKException("move_email()")
    except Exception as e:
      self.logger.error("Failed to move email: " + str(e))
      return False, str(e)

  def find_new_texts(self):
    imap = self.imap
    imap.select("inbox", readonly=False)
    # speed optimization: find emails only with vtext.com, etc
    resp, items = imap.search(None, "(UNSEEN)")
    mail_ids = []
    for block in items:
      mail_ids += block.split()
    emails = []
    for id in mail_ids[::-1]:
      data = self.get_data(id)
      if data.sender.lower().split("@")[1] in text_numbers:
        emails.append(data)
    self.logger.debug(f"Found {len(emails)} new texts (find_new_texts)")
    return emails

  def find_old_texts(self):
    imap = self.imap
    imap.select("inbox", readonly=False)
    # speed optimization: find emails only with vtext.com, etc
    resp, items = imap.search(None, "(SEEN)")
    mail_ids = []
    for block in items:
      mail_ids += block.split()
    emails = []
    for id in mail_ids[::-1]:
      data = self.get_data(id)
      if data.sender.lower().split("@")[1] in text_numbers:
        emails.append(data)
    self.logger.debug(f"Found {len(emails)} old texts (find_old_texts)")
    return emails

  def send_text(self,
                phone_number: str,
                content,
                subject="",
                carrier="verizon"):
    self.logger.warn("send_text is deprecated and might be removed if I feel like it")
    self.logger.info(f"Sending a text to {phone_number}")
    phone_number = re.findall("\\d+", phone_number)
    if type(phone_number) == list:
      phone_number = phone_number[0]
    try:
      receiver = phone_number + "@" + PROVIDERS[carrier]["sms"]
    except:
      raise ProviderNotFoundException(
        "Provider %s is not one of the valid providers" % carrier)
    message = f"""Subject: {subject}
{content}"""
    self.email_sender.sendmail(self.email_, [receiver], message)
    self.logger.info("Successfully texted {phone_number}")

  def send_mms_message(self,
                       phone_number: str,
                       text: str,
                       filename: str,
                       subject: str = "",
                       carrier="verizon"):
    self.logger.warn("send_mms_message is deprecated and might be removed if I feel like it")
    phone_number = re.findall("\\d+", phone_number)
    with open(filename, "rb") as file:
      data = file.read()
    msg = MIMEMultipart()
    if subject != "":
      msg["Subject"] = subject
    msg["From"] = self.email_
    try:
      receiver = [phone_number + "@" + PROVIDERS[carrier]["mms"]]
      if PROVIDERS[carrier]["mms_support"]:
        msg["To"] = phone_number + "@" + PROVIDERS[carrier]["mms"]
      else:
        raise ProviderWithoutMMSException(
          "Provider %s does not have mms support!" % carrier)
    except:
      raise ProviderNotFoundException(
        "Provider %s is not one of the valid providers" % carrier)

    msg.attach(MIMEText(text))
    msg.attach(MIMEImage(data, name=os.path.basename(filename)))

    self.email_sender.sendmail(self.email_, receiver, msg.as_string())

  def send_message(self,
                   phone_number: str,
                   body: str,
                   subject: str = "",
                   files=[],
                   carrier="verizon",
                   iter=0):
    self.logger.info(f"Sending message to {phone_number}...")
    try:
      data = []
      for file in files:
        with open(file, "rb") as f:
          data.append([file.lower(), f.read()])

      msg = MIMEMultipart()

      if subject != "":
        msg["Subject"] = subject
      msg["From"] = self.email_
      try:
        receiver = [phone_number + "@" + PROVIDERS[carrier]["mms"]]
        if PROVIDERS[carrier]["mms_support"]:
          msg["To"] = receiver[0]
        else:
          raise ProviderWithoutMMSException(
            "Provider %s does not have mms support!" % carrier)
      except:
        raise ProviderNotFoundException(
          "Provider %s is not one of the valid providers" % carrier)

      msg.attach(MIMEText(body))

      for file, binary_data in data:
        to_attach = MIMEBase("application", "octet-stream")
        to_attach.set_payload(binary_data)
        encoders.encode_base64(to_attach)
        to_attach.add_header(
          "Content-Disposition",
          'attachment; filename="%s"' % os.path.basename(file))
        msg.attach(to_attach)

      self.email_sender.sendmail(self.email_, receiver, msg.as_string())
      self.logger.info(f"Successfully sent a text to {phone_number}")
    except Exception as e:
      iter += 1
      if iter <= 2:
        self.logger.warn(f"Failed to send message, retrying... (attempt {iter + 1})")
        self.logger.warn("Might have been logged out from inactivity")
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(self.email_, self.password)
        imap.select(mailbox='inbox', readonly=False)
        self.imap = imap
  
        email_sender = smtplib.SMTP("smtp.gmail.com")
        email_sender.starttls(context=ssl.create_default_context())
        email_sender.login(self.email_, self.password)
        self.email_sender = email_sender
        return self.send_message(phone_number,
                                 body,
                                 subject=subject,
                                 files=files,
                                 carrier=carrier,
                                 iter=iter + 1)
      else:
        self.logger.error("Failed to send message. Reason: " + str(e))
        return False
  
  def download_attachments(self, email_id, download_dir, ignore_txt=True):
    self.logger.warn(
      "download_attachments is deprecated and will be removed in future versions! Use the Message class instead"
    )
    imap = self.imap
    res, data = imap.fetch(email_id, "(BODY.PEEK[])")
    if res != "OK":
      raise StatusNotOKException("download_attachments")
    body = data[0][1]
    mail = email.message_from_bytes(body)
    if mail.get_content_maintype() != "multipart": return

    paths = []
    for part in mail.walk():
      if part.get_content_maintype() != 'multipart' and part.get(
          'Content-Disposition') is not None:
        path = os.path.join(download_dir, part.get_filename())
        if not (ignore_txt and ".txt" in path):
          with open(path, 'wb') as file:
            file.write(part.get_payload(decode=True))
            paths.append(path)

    return paths

  def has_attachment(self, email_id, ignore_txt=True):
    self.logger.warn(
      "has_attachment is deprecated and will be removed in future versions! Use the Message class instead"
    )

    imap = self.imap
    res, data = imap.fetch(email_id, "(BODY.PEEK[])")
    if res != "OK":
      raise StatusNotOKException("has_attachment")
    body = data[0][1]
    mail = email.message_from_bytes(body)
    if mail.get_content_maintype() != "multipart": return

    paths = []
    for part in mail.walk():
      if part.get_content_maintype() != 'multipart' and part.get(
          'Content-Disposition') is not None:
        filename = part.get_filename()
        if not (ignore_txt and ".txt" in filename):
          paths.append(filename)

    return len(paths) > 0, paths

  def on_message(self, function):
    if type(function) != Message:
      self._on_message = function

  def run(self, delay_between_updates=10):
    self.create_texts_folder()
    self.move_texts()
    while True:
      try:
        new_texts = self.find_new_texts()
        for text in new_texts:
          if self._on_message is not None:
            self._on_message(text)
        if len(new_texts) > 0:
          self.move_texts()
        time.sleep(delay_between_updates)
      except imaplib.IMAP4.abort as e:
        self.logger.info("imaplib.IMAP4.abort error, logging in again. Error message in DEBUG level")
        self.logger.debug("Error text: " + str(e), exc_info=True)
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(self.email_, self.password)
        imap.select(mailbox='inbox', readonly=False)
        self.imap = imap

        email_sender = smtplib.SMTP("smtp.gmail.com")
        email_sender.starttls(context=ssl.create_default_context())
        email_sender.login(self.email_, self.password)
        self.email_sender = email_sender
