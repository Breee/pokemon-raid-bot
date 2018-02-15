import discord
import logging
logger = logging.getLogger('discord')


class ChannelMessagePair(object):
    def __init__(self, channel, message):
        if isinstance(channel, discord.Channel):
            self.channel = channel
        else:
            raise TypeError("The provided channel is not of type %s, but %s" % (discord.Channel.__name__, channel.__class__))

        if isinstance(message, discord.Message):
            self.message = message
        else:
            raise TypeError("The provided message is not of type %s, but %s" % (discord.Message.__name__, message.__class__))

    def __repr__(self):
        return "(Channel.name=%s, Message.content=%s)" % (self.channel.name, self.message.content)
