import logging
logger = logging.getLogger('discord')


class MessageStorage(object):
    def __init__(self,
                 messages,
                 pollmessage_id_to_storedmessage_id,
                 triggermessage_id_to_storedmessage_id,
                 pollmessage_id_to_poll_id):
        self.stored_messages = messages
        self.pollmessage_id_to_storedmessage_id = pollmessage_id_to_storedmessage_id
        self.triggermessage_id_to_storedmessage_id = triggermessage_id_to_storedmessage_id
        self.pollmessage_id_to_poll_id = pollmessage_id_to_poll_id
