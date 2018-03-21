from poll.emoji_storage import *
import logging
import time
import discord
logger = logging.getLogger('discord')


class PollCreationException(Exception):
    pass


class Poll(object):
    """
    A Poll object, used as parent for SinglePoll and MultiPoll.
    """

    def __init__(self, id, poll_title):
        self.poll_ID = id # some human readable id.
        self.creation_time = time.time() # timestamp
        self.poll_title = poll_title # string
        self.reactions = []
