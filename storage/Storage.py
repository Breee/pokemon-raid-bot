import logging
logger = logging.getLogger('discord')


class Storage(object):
    def __init__(self, message_storage, polls):
        self.message_storage = message_storage
        self.stored_polls = polls

