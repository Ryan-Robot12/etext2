# etext2
A modern text message handler in Python with MMS support.

Created by [smallguy89](https://pypi.org/user/smallguy89/) and [EpicCodeWizard](https://pypi.org/user/EpicCodeWizard/).
## Features
- Sync and async SMS and MMS sending.
- `on_message` decorator to create and run bots.
## Installation
Python 3.8 or higher is required.
```bash
pip3 install etext2
```
or
```bash
pip install etext2
```

## Quickstart
```py
from etext2.SMS_handler import EmailHandler

handler = EmailHandler(email="email@domain.com", password="your_password")

@handler.on_message
def on_message(message):
  if message == "ping":
    handler.send_message(message.sender, "pong", carrier="verizon")

handler.run()
```
## Functions
### Creating an EmailHandler Object
```py
from etext2.SMS_handler import EmailHandler
handler = EmailHandler(email="email@domain.com", password="your_password")
```
### Sending an SMS Message
```py
handler.send_message(phone_number, text_body, subject="", receiver_provider="verizon", files=[])
```
Arguments:
- ```phone_number``` - Number to send the text to. Unformatted or formatted accepted.
- ```text_body``` - Body of the text.
- ```subject``` - Subject of the message. Will be formatted as "(subject) text_body".
- ```receiver_provider```: Can be one of `['att', 'boost', 'c_spire', 'cricket', 'consumer_cellular', 'google_project_fi', 'metro', 'mint', 'page_plust', 'republic', 'sprint', 'straight_talk', 't_mobile', 'ting', 'tracfone', 'us_cellular', 'verizon', 'virgin_mobile', 'xfinity']` (NOTE: `verzion` and `t_mobile` work the best for US numbers).
- ```files```: List of files to send via MMS. The source of the file can be bytes, a path string, or a URL string. HTTP, HTTPS, FTP, and file URLs are supported.

Returns:
- A tuple (success, message)
  - ```success```: if the sending was successful or not
  - ```message```: the message (returned even if there was no error)

Sample call:
```py
handler.send_message("1234567890", "content", subject="Send using etext2", receiver_provider="verizon")
```
### Sending an MMS message
Use the same function as above, just attach files with the `files` parameter.

Sample call:
```py
handler.send_text("1234567890", text_body="content", subject="Send using etext2", receiver_provider="verizon", files=["image.png"])
```
Arguments:
- ```phone_number``` - Number to send the text to. Unformatted or formatted accepted.
- ```text_body``` - Body of the text.
- ```subject``` - Subject of the message. Will be formatted as "(subject) text_body".
- ```receiver_provider```: Can be one of `['att', 'boost', 'c_spire', 'cricket', 'consumer_cellular', 'google_project_fi', 'metro', 'mint', 'page_plust', 'republic', 'sprint', 'straight_talk', 't_mobile', 'ting', 'tracfone', 'us_cellular', 'verizon', 'virgin_mobile', 'xfinity']` (NOTE: `verzion` and `t_mobile` work the best for US numbers).
- ```files```: List of files to send via MMS. The source of the file can be bytes, a path string, or a URL string. HTTP, HTTPS, FTP, and file URLs are supported.

Returns:
- A tuple (success, message)
  - ```success```: if the sending was successful or not
  - ```message```: the message (returned even if there was no error)

### Advanced Usage Functions
- Creating the "texts" folder to store text messages:
  - ```handler.create_texts_folder()```
  - Automatically run on intialization
- Move all texts to the "texts" folder:
  - ```handler.move_texts()```
  - Used to clear texts out of the inbox and into the "texts" folder
  - Automatically run
- Get data from an email ID
  - ```handler.get_data(email_id, base64_decode=None)```
  - Returns a ```Message``` object containing the message data and ```None``` if there was an error
  - Arguments:
    - ```email_id``` - ID of the email. Binary string of a number (ex: b"1")
    - ```base64_decode``` - Whether or not to base64 decode the message body. Defaults to ```None``` and attempts to parse the email using try/except. If True, attempts to base64 decode the message body no matter what. Otherwise, it does not base64 decode it no matter what
  - Returns:
    - A ```Message``` object containing the message data or ```None``` if no emails were found
- Move an email to a destination label (used in ```move_texts()```)
  - ```handler.move_email(email_, destination_label)```
  - Labels an email as ```destination_label``` and removes it from the inbox
  - Arguments:
    - ```email_``` - Message object to move
    - ```destination_label``` - Label to move to, e.g. "texts"
  - Returns:
    - A tuple containing (```success```, ```message```)
      - ```success```: boolean
      - ```message```: If there was an error, this will be the message. Otherwise, it will be something like "Success"
- Get new texts statically
  - ```handler.find_new_texts(base64_decode=None)```
  - Arguments:
    - ```base64_decode``` - Whether or not to base64 decode the message body. Defaults to ```None``` and attempts to parse the email using try/except. If True, attempts to base64 decode the message body no matter what. Otherwise, it does not base64 decode it no matter what
  - Returns:
    - A list of Message objects containing emails in the inbox of the account
- Check if an email has any attachments (DEPRECATED - please use the Message class)
  - ```print(handler.has_attachment(email_id, ignore_txt=True))```
  - Arguments:
    - ```email_id``` - ID of the email. Should be a binary string (e.g. b"1")
    - ```ignore_txt``` - Defaults to True because some providers send the body of the message in a TXT file
  - Returns:
    - boolean of whether the message has any attachments
- Download message attachments (DEPRECATED - please use the Message class)
  - ```handler.download_attachments(email_id, download_dir, ignore_txt=True)```
  - Arguments:
    - ```email_id``` - ID of the email. Should be a binary string (e.g. b"1")
    - ```download_dir``` - Directory to download files to
    - ```ignore_txt``` - Whether or not to ignore .txt files
  - Returns:
    - A list of paths to the saved files
## The Message Class
### Purpose
- Provide easy access to message information, such as sender, attachments, and content.
- It is passed to functions registered with the ```handler.on_message``` decorator.
### Attributes
- ```message.has_attachment``` - Checks if the message has an attachment. This is not a method, this is an attribute
- ```message.download_attachments(download_dir, ignore_txt=True)```
  - Arguments:
    - ```download_dir``` - Directory to download the attachments to
    - ```ignore_txt``` - Whether or not to ignore .txt files. Defaults to true because some providers send the body of their messages in a .txt file.
  - Returns:
    - ```None``` if the response from imaplib's ```.fetch``` functon was not "OK"
    - Otherwise, a list of paths to the files downloaded
- ```print(str(message))```
  - The Message class has the equivalent of a toString function that returns the message dictionary as a string
  - Example:
  - Normal message: ```{'sender': 'number@provider.com', 'number': 'number', 'subject': 'message_subject', 'body': 'message example', 'email_id': b'1', 'has_attachments': False, 'attachments': []}```
  - MMS message: ```{'sender': 'number@provider.com', 'number': 'number', 'subject': 'message_subject', 'body': 'mms message example', 'email_id': b'1', 'has_attachments': True, 'attachments': ['IMG_0918.jpg']}```