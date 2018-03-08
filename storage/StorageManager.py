import logging
from storage.Storage import Storage
from messages.MessageManager import MessageManager
from storage.MessageStorage import MessageStorage
logger = logging.getLogger('discord')


class StorageManager(object):
    def __init__(self):
        self.storage = None

    def create_storage(self, message_manager, poll_factory):
        self.storage = Storage(message_storage=self.collect_messages(message_manager),
                               polls=self.collect_polls(poll_factory))

    def collect_messages(self, message_manager):
        if isinstance(MessageManager, message_manager):
            messages, pollmessage_id_to_storedmessage_id, triggermessage_id_to_storedmessage_id, pollmessage_id_to_poll_id = message_manager.get_data()
            message_storage = MessageStorage(messages=messages,
                                             pollmessage_id_to_storedmessage_id=pollmessage_id_to_storedmessage_id,
                                             triggermessage_id_to_storedmessage_id=triggermessage_id_to_storedmessage_id,
                                             pollmessage_id_to_poll_id=pollmessage_id_to_poll_id)
            return message_storage

    def collect_polls(self, poll_factory):
        return poll_factory.polls

