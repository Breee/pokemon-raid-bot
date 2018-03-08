from messages.StoredMessage import StoredMessage
import logging
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
        self.pollmessage_id_to_poll_id = dict()
        self.pollmessage_ID_to_StoredMessage_ID = dict()
        self.triggermessage_ID_to_StoredMessage_ID = dict()
        self.id_counter = len(self.messages)

    def create_message(self, trigger_message, poll_message, poll_id):
        self.pollmessage_id_to_poll_id[poll_message.id] = poll_id
        self.pollmessage_ID_to_StoredMessage_ID[poll_message.id] = self.id_counter
        self.triggermessage_ID_to_StoredMessage_ID[trigger_message.id] = self.id_counter

        stored_message = StoredMessage(message_id=self.id_counter,
                                       trigger_message=trigger_message,
                                       poll_message=poll_message,
                                       poll_id=poll_id)

        self.add_message(stored_message)
        self.id_counter += 1

    def get_message(self, msg_id=None, trigger_message_id=None, poll_message_id=None):
        if trigger_message_id and trigger_message_id in self.triggermessage_ID_to_StoredMessage_ID:
            msg_id = self.triggermessage_ID_to_StoredMessage_ID[trigger_message_id]
        elif poll_message_id and poll_message_id in self.pollmessage_ID_to_StoredMessage_ID:
            msg_id = self.pollmessage_ID_to_StoredMessage_ID[poll_message_id]

        if msg_id is not None:
            return self.messages[msg_id]
        else:
            return None

    def add_message(self, message):
        if isinstance(message, StoredMessage):
            self.messages[message.message_id] = message
        else:
            raise TypeError("parameter message is not of type %s but %s" % (StoredMessage.__name__, message.__class__))

    def delete_message(self, message_id):
        self.messages.pop(message_id, None)

    def update_message(self, message_id, trigger_message, poll_message, poll_id):
        pass

    def get_data(self):
        return self.messages, \
               self.pollmessage_ID_to_StoredMessage_ID, \
               self.triggermessage_ID_to_StoredMessage_ID, \
               self.pollmessage_id_to_poll_id



