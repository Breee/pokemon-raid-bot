"""
MIT License

Copyright (c) 2018 Breee@github

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from poll.emoji_storage import *
from poll.Poll import Poll, PollCreationException
import logging
import time
import discord

from globals.globals import LOGGER

class MultiPoll(Poll):
    """
    MultiPoll class, implements a poll with multiple vote options.
    """

    def __init__(self, id, poll_title, vote_options, reaction_to_user=dict(), user_to_amount=dict()):
        super().__init__(id, poll_title)

        self.reaction_to_embed_field = dict()  # dict that maps reactions to embed field names.
        if vote_options:
            self.vote_options = vote_options # list of strings
        else:
            raise PollCreationException("ERROR 1:\n no vote options provided.")
        self.embed = self.create_embed(vote_options=vote_options) # embed to represent the poll.
        self.original_embed = self.create_embed(vote_options=vote_options) # embed to represent the poll.
        self.reaction_to_user = reaction_to_user
        # list of users which come not alone
        self.user_to_amount = user_to_amount

    def create_embed(self, vote_options):
        """
        Function which shall create a new embed and store it in self.embed.
        :return:
        """
        embed = discord.Embed(colour=discord.Colour(0x700000))
        for i in range(len(vote_options)):
            emoji = EmojiStorage.NUMBER_TO_LETTEREMOJI[i]
            vote_option = vote_options[i]
            if not vote_option.startswith(emoji):
                field_name = "%s %s" % (emoji, vote_option)
            else:
                field_name = vote_option

            embed.add_field(name=field_name, value="-", inline=False)
            self.reaction_to_embed_field[emoji] = field_name
        return embed

    def update_embed(self):
        """
        Function which shall update self.embed.
        :return:
        """
        old_embed = self.original_embed
        new_embed = discord.Embed(title=old_embed.title, colour=discord.Colour(0x700000),
                                  description=old_embed.description)
        # list of users which reacted to a certain field in the embed
        self.reaction_to_user = dict()
        # list of users which come not alone
        self.user_to_amount = dict()
        # for each reaction, user tuple in reactions, we fill the dictionaries reaction_to_user, people
        # _to_user.
        for reaction, user in self.reactions:
            username = user.display_name
            # add a user to reaction_to_user if he reacted with an emoji that equals an emoji mapped
            # to a field in the embed
            if reaction.emoji in self.reaction_to_embed_field.keys():
                self.reaction_to_user.setdefault(self.reaction_to_embed_field[reaction.emoji], []).append(username)
                if username not in self.user_to_amount.keys():
                    # by default every user comes alone. i.e. counts as one person.
                    self.user_to_amount[username] = 1
            # add a user to people_to_user, if he reacted with an emoji that equals an emoji of the
            # PEOPLE_EMOJI_TO_NUMBER dict.
            if EmojiStorage.is_people_emoji(emoji=reaction.emoji):
                if username in self.user_to_amount:
                    self.user_to_amount[username] += EmojiStorage.get_people_empji_value(reaction.emoji)
                else:
                    self.user_to_amount[username] = 1 + EmojiStorage.get_people_empji_value(reaction.emoji)
        # create fields
        for field in old_embed.fields:
            if field.name in self.reaction_to_user.keys():
                total = 0
                people = ""
                for i, user in enumerate(self.reaction_to_user[field.name]):
                    people += user + " [%d]" % self.user_to_amount[user]
                    if i < len(self.reaction_to_user[field.name]) - 1:
                        people += ", "
                    total += self.user_to_amount[user]
                new_embed.add_field(name=field.name + " [%d]" % total, value=people, inline=False)
            else:
                new_embed.add_field(name=field.name, value="-", inline=False)

        self.embed = new_embed

    def edit_poll(self, poll_title, vote_options):
        pass










