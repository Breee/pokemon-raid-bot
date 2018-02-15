import logging
import time
import discord
logger = logging.getLogger('discord')

class Poll(object):

    def __init__(self, id, poll_title, vote_options):
        self.poll_ID = id # some human readable id.
        self.creation_time = time.time() # timestamp
        self.poll_title = poll_title # string
        self.vote_options = vote_options # list of strings
        self.embed = self.create_embed(vote_options=vote_options) # embed to represent the poll.
        self.reaction_to_embed_field = dict() # dict that maps reactions to embed field names.


    def create_embed(self, vote_options):
        """
        Function which shall create a new embed and store it in self.embed.
        :return:
        """
        pass

    def update_embed(self,vote_options):
        """
        Function which shall update self.embed.
        :return:
        """
        pass

    def update_poll(self, poll_title, vote_options):
        pass








