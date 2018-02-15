from messages.StoredMessage import StoredMessage
import logging
import time
logger = logging.getLogger('discord')


class MessageManager(object):

    def __init__(self, messages=None):
        # polls passed shall be a dictionary of the form { poll_ID -> poll}
        if isinstance(messages, dict):
            self.messages = messages
        elif messages is None:
            self.messages = dict()
        else:
            raise TypeError(
                "The provided messages object is not of type %s, but %s.\n"
                "We expect a dictionary oft the form: { message_ID -> message}" % (dict.__name__, messages))
        self.pollmessage_id_to_pollmessage = dict()
        self.triggermessage_id_to_pollmessage = dict()
        self.pollmessage_id_to_poll_id = dict()
        self.id_counter = len(self.messages)

    def create_message(self, trigger_message, poll_message, poll_id):
        self.pollmessage_id_to_pollmessage[poll_message.id] = poll_message
        self.triggermessage_id_to_pollmessage[trigger_message.id] = poll_message
        self.pollmessage_id_to_poll_id[poll_message.id] = poll_id
        self.id_counter += 1

    def add_message(self, message):
        if isinstance(message, StoredMessage):
            self.messages[message.message_id] = message
        else:
            raise TypeError("parameter message is not of type %s but %s" % (StoredMessage.__name__, message.__class__))

    def delete_message(self, message_id):
        self.messages.pop(message_id, None)

    def update_message(self, message_id):
        pass



