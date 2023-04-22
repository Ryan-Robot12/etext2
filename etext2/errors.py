import logging, json

with open("etext2/providers.json") as file:
  PROVIDERS = json.load(file)


class EmailNotFoundException(Exception):
  def __init__(self, email_id):
    logger = logging.getLogger("EmailHandler")
    logger.error(f"Email with ID {email_id} was not found")
    super().__init__(f"Email with ID {email_id} was not found")


class ProviderWithoutMMSException(Exception):

  def __init__(self, provider):
    logger = logging.getLogger("EmailHandler")
    logger.error(f"Provider '{provider}' does not have MMS support")
    super().__init__(f"Provider '{provider}' does not have MMS support")


class ProviderNotFoundException(Exception):

  def __init__(self, provider):
    logger = logging.getLogger("EmailHandler")
    logger.error(f"Provider '{provider}' was not found. Make sure it is one of the following: ["
      + ", ".join(PROVIDERS) + "]")
    super().__init__(
      f"Provider '{provider}' was not found. Make sure it is one of the following: ["
      + ", ".join(PROVIDERS) + "]")


class StatusNotOKException(Exception):

  def __init__(self, function):
    logger = logging.getLogger("EmailHandler")
    logger.error(f"OK status not returned for function {function}!")
    super().__init__(
      f"OK status not returned for function {function}!")
