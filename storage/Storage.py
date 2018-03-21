import logging
import sqlite3
logger = logging.getLogger('discord')


class Storage(object):
    def __init__(self, message_manager, poll_factory, client_messages):
        self.message_manager = message_manager
        self.poll_factory = poll_factory
        self.client_messages = client_messages
