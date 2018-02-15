import discord
import logging
import time
logger = logging.getLogger('discord')


class StoredMessage(object):
    def __init__(self, message_id, trigger_message, poll_message, poll_id):
        self.message_id = message_id
        self.creation_time = time.time()
        self.trigger_message = trigger_message
        self.poll_message = poll_message
        self.poll_id = poll_id

