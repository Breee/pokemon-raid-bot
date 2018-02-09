import discord
import logging
logger = logging.getLogger('discord')


class ReactionUserPair(object):
    def __init__(self, reaction, user):
        if isinstance(reaction, discord.Reaction):
            self.reaction = reaction
        else:
            raise TypeError("The provided reaction is not of type %s, but %s" % (discord.Reaction.__name__, reaction.__class__))

        if isinstance(user, discord.User):
            self.user = user
        else:
            raise TypeError("The provided user is not of type %s, but %s" % (discord.User.__name__, user.__class__))

    def __repr__(self):
        """
        >>> pair = ReactionUserPair(discord.Reaction(emoji=':thumbsup:'), discord.User(username='Testman'))
        >>> pair.__repr__()
        '(Reaction.emoji=:thumbsup:, User.name=Testman)'

        :return:
        """
        return "(Reaction.emoji=%s, User.name=%s)" % (self.reaction.emoji, self.user.name)
