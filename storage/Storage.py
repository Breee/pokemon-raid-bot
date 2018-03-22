import logging
from storage.MessageStorage import MessageStorage
logger = logging.getLogger('discord')


class Storage(object):
    def __init__(self, message_manager, poll_factory, client_messages):
        self.message_storage = MessageStorage(messages=message_manager.messages,
                                              pollmessage_id_to_poll_id=message_manager.pollmessage_id_to_poll_id,
                                              pollmessage_id_to_storedmessage_id=message_manager.pollmessage_id_to_storedmessage_id,
                                              triggermessage_id_to_storedmessage_id=message_manager.triggermessage_id_to_storedmessage_id)
        self.polls = poll_factory.polls
        self.client_messages = client_messages
