import discord
import logging
logger = logging.getLogger('discord')


class Message(object):
    def __init__(self, message_id, trigger_message, poll_message, poll_id):
        self.message_id = message_id
        self.trigger_message = trigger_message
        self.poll_message = poll_message
        self.poll_id = poll_id

