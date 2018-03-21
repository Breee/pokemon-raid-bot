import logging
import time
logger = logging.getLogger('discord')


class StoredMessage(object):
    def __init__(self, id, trigger_message, poll_message, poll_id):
        self.id = id
        self.creation_time = time.time()
        self.trigger_message = trigger_message
        self.poll_message = poll_message
        self.poll_id = poll_id

