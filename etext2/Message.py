import json, os
from etext2.errors import *

with open("etext2/mimetypes.json") as file:
  MIMETYPES = json.load(file)


class Message:
  has_attachment = False
  attachments = []
  date_sent = None
  subject = None
  number = None
  sender = None
  data = None
  html = None
  body = None
  id = None

  def __init__(self, imap, data, b64_decode=None):
    self.data = data

    self.has_attachment = len(data["attachments"]) > 0
    self.attachments = data["attachments"]
    self.date_sent = data["date_sent"]
    self.subject = data["subject"]
    self.sender = data["sender"]
    self.number = data["number"]
    self.body = data["body"]
    self.html = data["html"]
    self.id = data["id"]

  def __str__(self):
    tmp = self.data
    tmp["attachments"] = [file.filename for file in tmp["attachments"]]
    return str(tmp)

  def download_attachments(self, download_dir, filenames=[]):
    if not self.has_attachment:
      return None
    else:
      attachments = []
      for i, attachment in enumerate(self.attachments):
        if attachment.filename == "":
          for type in MIMETYPES:
            if attachment.mimetype == type:
              extension = MIMETYPES[type]
          filename = os.path.join(download_dir, f"saved_file_{i}{extension}")
          with open(filename, "wb") as file:
            file.write(attachment.content)
            attachments.append(filename)
        else:
          filename = os.path.join(download_dir, attachment.filename)
          with open(filename, "wb") as file:
            file.write(attachment.content)
            attachments.append(filename)
      return attachments
