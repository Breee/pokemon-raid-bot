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

from poll.Poll import Poll
from poll.MultiPoll import MultiPoll
from poll.SinglePoll import SinglePoll
import logging
import discord
from globals.globals import LOGGER
import database.dbmodels as models
import uuid

class PollFactory(object):
    """
    A Class that implements a PollFactory, used to create and update Poll objects.
    """

    def __init__(self, polls=None):
        # polls passed shall be a dictionary of the form { poll_ID -> poll}
        if isinstance(polls, dict):
            self.polls = polls
        elif polls is None:
            self.polls = dict()
        else:
            raise TypeError(
                "The provided polls is not of type %s, but %s.\n"
                "We expect a dictionary oft the form: { poll_ID -> poll}" % (dict.__name__, polls))
        self.id_counter = len(self.polls)

    def create_multi_poll(self, poll_title, vote_options, id=None, reaction_to_user=dict(), user_to_amount=dict()):
        """
        Function which creates a new MultiPoll object and stores it in self.polls
        :param poll_title: String which denotes the title of a poll
        :param vote_options: List of Strings which denote the vote options.
        :return: void
        """
        if not id:
            id = str(uuid.uuid4())
        # create a new Poll object.
        new_poll = MultiPoll(id=id, poll_title=poll_title, vote_options=vote_options, reaction_to_user=reaction_to_user,user_to_amount=user_to_amount)
        self.add_poll(poll_id=id, poll=new_poll)
        LOGGER.info("Created poll %s" % new_poll.poll_id)
        return new_poll


    def create_single_poll(self,poll_title, id=None):
        """
        Function which creates a new SinglePoll object and stores it in self.polls
        :param poll_title: String which denotes the title of a poll
        :param vote_options: List of Strings which denote the vote options.
        :return: void
        """
        # create a new Poll object.
        if not id:
            id = str(uuid.uuid4())
        new_poll = SinglePoll(id=id, poll_title=poll_title)
        self.add_poll(poll_id=id, poll=new_poll)
        self.id_counter += 1
        return new_poll


    def add_poll(self, poll_id, poll):
        """
        Helper function which adds polls to self.polls and verifies that the provided poll is indeed a Poll object.
        :param poll_id:
        :param poll:
        :return:
        """
        if isinstance(poll, Poll):
            self.polls[poll_id] = poll
        else:
            raise TypeError(
                "The provided poll is not of type %s, but %s.\n" % (Poll.__name__, poll))

    def get_poll(self, poll_id):
        """
        Function which will return a poll.
        :param poll_id: Integer.
        :return: Poll object with the id "poll_id".
        """
        return self.polls[poll_id]

    def restore_polls(self, polls):
        poll_dict = dict()
        for poll in polls:
            restored_poll = None
            if isinstance(poll, models.Poll):
                if not poll.vote_options:
                    restored_poll = self.create_single_poll(poll_title=poll.name, id=poll.external_id)
                elif len(poll.vote_options) > 0:
                    restored_poll = self.create_multi_poll(poll_title=poll.name, vote_options=poll.vote_options, id=poll.external_id, reaction_to_user=poll.reaction_to_user, user_to_amount=poll.user_to_amount)
                if restored_poll:
                    poll_dict[poll.external_id] = restored_poll

        self.polls = poll_dict
        self.id_counter = len(poll_dict)
