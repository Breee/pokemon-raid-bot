from messages.Message import Message
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
        self.id_counter = len(self.messages)

    def create_message(self, trigger_message, poll_message, poll_id):
        self.add_message(Message(message_id=self.id_counter,
                                 trigger_message=trigger_message,
                                 poll_message=poll_message,
                                 poll_id=poll_id))

    def add_message(self, message):
        if isinstance(message, Message):
            self.messages[message.message_id] = message
        else:
            raise TypeError("parameter message is not of type %s but %s" % (Message.__name__, message.__class__))

    def delete_message(self, message_id):
        self.messages.pop(message_id, None)

    def update_message(self, message_id):
        pass



