import logging
import pickle
import os
from storage.Storage import Storage
LOGGER = logging.getLogger('discord')


class StorageManager(object):
    def __init__(self):
        self.storage = None
        self.dump_file_name = "storage.pickle"

    def update_storage(self, message_manager, poll_factory, client_messages):
        self.storage = Storage(message_manager=message_manager,
                               poll_factory=poll_factory,
                               client_messages=client_messages)
        self.dump_storage()

    def dump_storage(self):
        LOGGER.info("Dumping Storage to %s" % self.dump_file_name)
        with open(self.dump_file_name, 'wb') as dump:
            pickle.dump(self.storage, dump, protocol=pickle.HIGHEST_PROTOCOL)
            LOGGER.info("Dumping Storage was successful")

    def load_storage(self):
        LOGGER.info("Loading Storage from %s" % self.dump_file_name)
        if os.path.isfile(self.dump_file_name):
            if os.stat(self.dump_file_name).st_size != 0:
                with open(self.dump_file_name, 'rb') as dump:
                    self.storage = pickle.load(dump)
                    LOGGER.info("Loading Storage was successful.")


