import logging
import pickle
import os
from storage.Storage import Storage
logger = logging.getLogger('discord')


class StorageManager(object):
    def __init__(self):
        self.storage = None
        self.dump_file_name = "storage.pickle"

    def update_storage(self, message_manager, poll_factory,client_messages):
        self.storage = Storage(message_manager=message_manager,
                               poll_factory=poll_factory,
                               client_messages=client_messages)
        self.dump_storage()

    def dump_storage(self):
        #with open(self.dump_file_name, 'wb') as dump:
         #   pickle.dump(self.storage, dump, protocol=pickle.HIGHEST_PROTOCOL)
        pass

    def load_storage(self):
        #if os.stat(self.dump_file_name).st_size != 0:
        #    with open(self.dump_file_name, 'rb') as dump:
        #        self.storage = pickle.load(dump)
        pass

