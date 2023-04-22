from etext2.SMS_handler import EmailHandler
import logging, shutil, os
"""
Text sender/receiver using smtplib and imaplib
Dependencies:
- fast_mail_parser (https://pypi.org/project/fast-mail-parser/)

Instructions for running:
- Change Set EMAIL below
- Set PASS as an environmental variable
- Run the code
- Text your email (e.g. send "testing" to your_email@domain.com)
- Your phone should get a text in return with the content in uppercase
"""

EMAIL = "email@domain.com"
try:
  PASS = os.environ["PASS"]
except:
  raise Exception("Please set PASS as an environmental variable!")

def clear(folder):
  for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
      if os.path.isfile(file_path) or os.path.islink(file_path):
        os.unlink(file_path)
      elif os.path.isdir(file_path):
        shutil.rmtree(file_path)
    except Exception as e:
      print('Failed to delete %s. Reason: %s' % (file_path, e))


def main():
  handler = EmailHandler(EMAIL, PASS, loglevel=logging.DEBUG)

  @handler.on_message
  def on_message(message):
    print("New message: " + str(message))
    clear("saved_files")
    if message.has_attachment:
      message.download_attachments("saved_files")
    handler.send_message(
      message.number,
      message.body[:100].upper(),
      subject="response in uppercase",
      files=["saved_files/" + file for file in os.listdir("saved_files")])

  handler.run()


if __name__ == "__main__":
  main()
