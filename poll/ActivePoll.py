import logging
import time
logger = logging.getLogger('discord')

class ActivePoll(object):

    def __init__(self, id, title, vote_options):
        self.poll_ID = id # some human readable id.
        self.creation_time = time.time() # timestamp
        self.channel_to_message = dict()  # dict channel objects --> message objects
        self.poll_title = title # string
        self.vote_options = vote_options # list of strings
        self.embed = None # embed to represent the poll.
        self.reaction_to_embed_field = dict() # dict that maps reactions to embed field names.


    def create_embed(self):
        """
        Function which shall create a new embed and store it in self.embed.
        :return:
        """
        pass

    def update_embed(self):
        """
        Function which shall update self.embed.
        :return:
        """
        pass

    def add_channel_to_massage_pair(self, channel_to_message_pair):
        """
        Function which shall add Channel/Message of a ChannelMessagePair object to self.channel_to_message.
        :param channel_to_message_pair:
        :return:
        """
        pass

    def delete_message_from_channel(self, message_id, channel_id):
        """
         Function which shall remove a message from a channel in self.channel_to_message.
         :param channel_to_message_pair:
         :return:
        """
        pass

    def delete_all_messages(self):
        """
         Function which shall delete all messages in all channels.
         :param channel_to_message_pair:
         :return:
        """
        pass

    def update_all_messages(self):
        """
        Function which shall update all messages in all channels.
        :return:
        """
        pass






