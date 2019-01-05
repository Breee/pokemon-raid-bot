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
from globals.globals import LOGGER


class SinglePoll(Poll):
    """
     SinglePoll class, implements a poll with no vote options.
    """

    def __init__(self, id, poll_title):
        super().__init__(id, poll_title)
        self.summary_message = ""

    def create_summary_message(self):
        """
        Function which shall update self.embed.
        :return:
        """
        # list of users which come not alone
        people_to_user = {}
        # for each reaction, user tuple in reactions, we fill the dictionaries reaction_to_user, people
        # _to_user.
        for reaction, user in self.reactions:
            username = user.mention
            # add a user to people_to_user, if he reacted with an emoji that equals an emoji of the
            # PEOPLE_EMOJI_TO_NUMBER dict.
            if reaction.emoji in EmojiStorage.EMOJI_TO_NUMBER.keys():
                if username in people_to_user.keys():
                    people_to_user[username] += (1 + EmojiStorage.EMOJI_TO_NUMBER[reaction.emoji])
                else:
                    people_to_user[username] = 1 + EmojiStorage.EMOJI_TO_NUMBER[reaction.emoji]

        msg = "**%s**\n" \
              "\n" \
              "__**Raiders:**__\n" % (self.poll_title)
        counter = 0
        total = 0
        for user, amount in people_to_user.items():
            counter += 1
            total += amount
            msg += "%s[%d]" % (user, amount)
            if counter < len(people_to_user):
                msg += ", "
        msg += "\n" \
               "\n" \
               "__**Total Raiders: %d**__" % total

        self.summary_message = msg










