""" Application that provides functionality for the Telegram bot. """
import logging.config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class App:
    def __init__(self, parameter: str):
        self.parameter = parameter

    def run(self, message_text: str):
        logger.info(f"Received message: {message_text}")
        return f"Message text: {message_text}\nApp's parameter: {self.parameter}"
