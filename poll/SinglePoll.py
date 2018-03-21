from poll.emoji_storage import *
from poll.Poll import Poll,PollCreationException
import logging
import time
logger = logging.getLogger('discord')


class SinglePoll(Poll):

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
            if reaction.emoji in EMOJI_TO_NUMBER.keys():
                if username in people_to_user.keys():
                    people_to_user[username] += (1+ EMOJI_TO_NUMBER[reaction.emoji])
                else:
                    people_to_user[username] = 1 + EMOJI_TO_NUMBER[reaction.emoji]

        msg = "Poll #%d\n" \
              "***%s***\n" \
              "\n" \
              "__**Raiders:**__\n" % (self.poll_ID, self.poll_title.lstrip("raid "))
        counter = 0
        total = 0
        for user, amount in people_to_user.items():
            counter += 1
            total += amount
            if counter < len(people_to_user):
                msg += ", "
            msg += "%s[%d]" % (user, amount)
        msg += "\n" \
               "\n" \
               "__**Total Raiders: %d**__" % total

        self.summary_message = msg










