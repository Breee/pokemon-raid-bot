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

from config.Configuration import Configuration
from messages.MessageManager import MessageManager
from storage.StorageManager import StorageManager
from poll.PollFactory import PollFactory
from poll.Poll import Poll
from poll.MultiPoll import MultiPoll
from poll.SinglePoll import SinglePoll
from discord.ext import commands
from discord.ext.commands import Context, CommandError, CommandNotFound
from discord.ext.commands.view import StringView
import asyncio
from utils import replace_quotes
from poll.emoji_storage import EmojiStorage
import discord
import datetime
import aiohttp
import logging
import os
import copy

LOGGER = logging.getLogger('discord')
if os.path.isfile('help_msg.txt'):
    with open('help_msg.txt', 'r') as helpfile:
        HELP_MSG = helpfile.read()

BANNED_USERS = []
if os.path.isfile('banned_users.txt'):
    with open('banned_users.txt', 'r') as banned_users:
        for line in banned_users:
            BANNED_USERS.append(line)

class PollBot(commands.Bot):
    def __init__(self, prefix, description, config_file):
        super().__init__(command_prefix=prefix, description=description, pm_help=None, help_attrs=dict(hidden=True))
        self.config = Configuration(config_file)
        self.storage_manager = StorageManager()
        self.poll_factory = PollFactory()
        self.message_manager = MessageManager()
        self.add_command(self.ping)
        self.add_command(self.poll)
        self.add_command(self.uptime)
        self.add_command(self.removeoutdated)
        self.add_command(self.readpoll)
        self.remove_command("help")
        self.add_command(self.help)
        self.start_time = 0
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.use_custom_emojies = True

    async def on_ready(self):
        LOGGER.info("Bot is ready.")
        self.start_time = datetime.datetime.utcnow()
        await self.init_custom_emojies()
        await self.change_presence(game=discord.Game(name=self.config.playing))
        await self.restore_messages_and_polls()

    async def init_custom_emojies(self):
        LOGGER.info("Init custom emojies")
        if self.use_custom_emojies:
            EmojiStorage.PEOPLE_EMOJI_TO_NUMBER = dict()
            server_emojis = self.get_all_emojis()
            for emoji in server_emojis:
                number = None
                if "rq_plus_one" in emoji.name:
                    number = 1
                elif "rq_plus_two" in emoji.name:
                    number = 2
                elif "rq_plus_three" in emoji.name:
                    number = 3
                elif "rq_plus_four" in emoji.name:
                    number = 4
                if number is not None and emoji not in EmojiStorage.PEOPLE_EMOJI_TO_NUMBER:
                    EmojiStorage.PEOPLE_EMOJI_TO_NUMBER[emoji] = number
        if len(EmojiStorage.PEOPLE_EMOJI_TO_NUMBER) != 4:
            EmojiStorage.PEOPLE_EMOJI_TO_NUMBER = EmojiStorage.DEFAULT_PEOPLE_EMOJI_TO_NUMBER

    def run(self):
        super().run(self.config.token, reconnect=True)

    async def close(self):
        await super().close()
        await self.session.close()

    async def on_resumed(self):
        print('resumed...')

    @commands.command(hidden=True)
    async def ping(self):
        await self.say("pong!")

    @commands.command(hidden=True)
    async def uptime(self):
        await self.say("Online for %s" % str(datetime.datetime.utcnow() - self.start_time))

    @commands.command(pass_context=True)
    async def help(self, ctx, here=None):
        if not here:
            await self.send_message(destination=ctx.message.author, content=HELP_MSG)
            #await self.delete_message(ctx.message)
        else:
            await self.say(HELP_MSG)
            # await self.delete_message(ctx.message)

    @commands.command(pass_context=True)
    async def poll(self, ctx, poll_title, *vote_options):
        if str(ctx.message.author) in BANNED_USERS:
            LOGGER.warning("Denied creation of poll, User %s is banned" % ctx.message.author)
            return
        await self.create_multi_poll(trigger_message=ctx.message, poll_title=poll_title, vote_options=vote_options)
        self.storage_manager.update_storage(message_manager=self.message_manager,
                                            poll_factory=self.poll_factory,
                                            client_messages=self.messages)

    @commands.command(hidden=True)
    async def removeoutdated(self, time):
        self.message_manager.dump_and_remove(float(time))
        self.storage_manager.update_storage(message_manager=self.message_manager,
                                            poll_factory=self.poll_factory,
                                            client_messages=self.messages)

    @commands.command(pass_context=True)
    async def readpoll(self,ctx, trigger_id, msg_id, *vote_options):
        msg = await self.get_message_if_exists(channel=ctx.message.channel,msg_id=msg_id)
        trigger = await self.get_message_if_exists(channel=ctx.message.channel, msg_id=trigger_id)
        title = msg.content.replace("Poll for", "")
        poll = self.poll_factory.create_multi_poll(poll_title=title, vote_options=vote_options)
        poll.update_embed()
        self.messages.append(msg)
        await self.edit_msg(msg, poll.embed)
        self.message_manager.create_message(trigger_message=trigger,
                                            poll_message=msg, poll_id=poll.poll_ID)
        await self.update_poll_after_restart(msg_id,msg.reactions)

    async def create_multi_poll(self, trigger_message, poll_title, vote_options):
        """
        Function that creates a new MultiPoll and posts it.
        :param trigger_message: Message which triggered the creation of the poll
        :param poll_title: Title of the poll
        :param vote_options: List of string which contains vote options.
        :return:
        """
        LOGGER.info("Creating Multipoll.\n"
                    "trigger_message: %s,\n"
                    "poll_title: %s,\n"
                    "vote_options: %s" % (trigger_message.content, poll_title, vote_options))
        # Create a new poll and post it.
        poll = self.poll_factory.create_multi_poll(poll_title=poll_title, vote_options=vote_options)
        poll_message = await self.send_message(trigger_message.channel,
                                               content="Poll for **%s**" % (poll_title),
                                               embed=poll.embed)
        self.message_manager.create_message(trigger_message=trigger_message,
                                            poll_message=poll_message, poll_id=poll.poll_ID)

        # add vote emojies as reaction
        sorted_emoji = [(k, EmojiStorage.LETTEREMOJI_TO_NUMBER[k]) for k in sorted(EmojiStorage.LETTEREMOJI_TO_NUMBER, key=EmojiStorage.LETTEREMOJI_TO_NUMBER.get)]
        for emoji, n in sorted_emoji:
            if n <= len(vote_options) - 1:
                await self.add_reaction(poll_message, emoji)

        # add people emojie as reaction
        sorted_people_emoji = [(k, EmojiStorage.PEOPLE_EMOJI_TO_NUMBER[k]) for k in
                               sorted(EmojiStorage.PEOPLE_EMOJI_TO_NUMBER, key=EmojiStorage.PEOPLE_EMOJI_TO_NUMBER.get)]
        for emoji, n in sorted_people_emoji:
            await self.add_reaction(poll_message, emoji)
        LOGGER.info("Done.")

    async def create_single_poll(self, trigger_message, poll_title):
        """
        Function that creates a new Singlepoll and posts it.
        :param trigger_message: Message which triggered the creation of the poll
        :param poll_title: Title of the poll
        :return:
        """
        LOGGER.info("Creating SinglePoll.\n"
                    "trigger_message: %s" % trigger_message.content)
        # Create a new poll and post it.
        poll = self.poll_factory.create_single_poll(poll_title=poll_title)
        poll.create_summary_message()
        poll_message = await self.send_message(trigger_message.channel,
                                               content=poll.summary_message)

        self.message_manager.create_message(trigger_message=trigger_message,
                                            poll_message=poll_message, poll_id=poll.poll_ID)

        # add people emojie as reaction
        sorted_people_emoji = [(k, EmojiStorage.EMOJI_TO_NUMBER[k]) for k in
                               sorted(EmojiStorage.EMOJI_TO_NUMBER, key=EmojiStorage.EMOJI_TO_NUMBER.get)]
        for emoji, n in sorted_people_emoji:
            if n < 4:
                await self.add_reaction(poll_message, emoji)

    async def on_reaction_add(self, reaction, user):
        """
        Function which handles reactions added by users, used to update existing polls.
        :param reaction: reaction message.
        :param user: user which added a reaction.
        :return:
        """
        if user != self.user:
            if str(user) in BANNED_USERS:
                LOGGER.warning("Denied reaction, User %s is banned" % user)
                return
            # reaction has to be part of the vote emojis/ people emojis
            if reaction.emoji in EmojiStorage.LETTEREMOJI_TO_NUMBER or EmojiStorage.is_people_emoji(reaction.emoji) or reaction.emoji in EmojiStorage.EMOJI_TO_NUMBER:
                stored_message = self.message_manager.get_message(poll_message_id=reaction.message.id)
                if stored_message:
                    # get poll
                    poll_id = self.message_manager.pollmessage_id_to_poll_id[reaction.message.id]
                    # add reactions
                    poll = self.poll_factory.polls[poll_id]
                    poll.reactions.append((reaction, user))
                    # edit poll
                    if isinstance(poll, MultiPoll):
                        poll.update_embed()
                        await self.edit_msg(reaction.message, poll.embed)
                    elif isinstance(poll, SinglePoll):
                        poll.create_summary_message()
                        await self.edit_message(reaction.message, poll.summary_message)
                    self.storage_manager.update_storage(message_manager=self.message_manager,
                                                        poll_factory=self.poll_factory, client_messages=self.messages)

    async def on_reaction_remove(self, reaction, user):
        """
        Function which handles reactions removed by users, used to update existing polls.
        :param reaction: reaction message.
        :param user: user which added a reaction.
        :return:
        """
        if user != self.user:
            if str(user) in BANNED_USERS:
                LOGGER.warning("Denied reaction, User %s is banned" % user)
                return
            if reaction.emoji in EmojiStorage.LETTEREMOJI_TO_NUMBER or EmojiStorage.is_people_emoji(reaction.emoji) or reaction.emoji in EmojiStorage.EMOJI_TO_NUMBER:
                stored_message = self.message_manager.get_message(poll_message_id=reaction.message.id)
                if stored_message:
                    # get poll
                    poll_id =  self.message_manager.pollmessage_id_to_poll_id[reaction.message.id]
                    # add reactions
                    poll = self.poll_factory.polls[poll_id]
                    poll.reactions.remove((reaction, user))
                    # edit poll
                    if isinstance(poll, MultiPoll):
                        poll.update_embed()
                        await self.edit_msg(reaction.message, poll.embed)
                    elif isinstance(poll, SinglePoll):
                        poll.create_summary_message()
                        await self.edit_message(reaction.message, poll.summary_message)
                    self.storage_manager.update_storage(message_manager=self.message_manager,
                                                        poll_factory=self.poll_factory, client_messages=self.messages)

    async def on_message_delete(self, message):
        """
        Function which handles messages that have been deleted.
        :param message: deleted message.
        :return:
        """
        if isinstance(message, discord.Message):
            # get the stored message!
            stored_message = self.message_manager.get_message(trigger_message_id=message.id)
            if stored_message is not None:
                await self.delete_pollmessage(poll_message=stored_message.poll_message,
                                              trigger_message=stored_message.trigger_message,
                                              stored_message=stored_message,
                                              update_storage=True)

    async def delete_pollmessage(self, poll_message, trigger_message,
                                 stored_message=None,
                                 post_notification=True,
                                 update_storage=False):
        """
        Fucntion which deletes a pollmessage
        :param poll_message: message which contains the poll.
        :param trigger_message: message which triggered the creation of the poll.
        :param stored_message: StoredMessage object.
        :param post_notification: Boolean which determines whether a notification about the deletion gets posted or not.
        :return:

        """
        # get poll
        poll_id = self.message_manager.pollmessage_id_to_poll_id[poll_message.id]
        # add reactions
        poll = self.poll_factory.polls[poll_id]
        try:
            await self.delete_message(poll_message)
        except discord.NotFound:
            LOGGER.info("Pollmessage #%s for poll #%d does not exists anymore" % (poll_message.id, poll_id))

        if post_notification:
            await self.send_message(trigger_message.channel,
                                    content="Deleted poll #%s: %s" % (poll.poll_ID, poll.poll_title))
        # remove the message
        if stored_message:
            self.message_manager.delete_message(stored_message.id)
        if update_storage:
            self.storage_manager.update_storage(message_manager=self.message_manager,
                                                poll_factory=self.poll_factory,
                                                client_messages=self.messages)

    async def on_message_edit(self, before, after):
        """
        Fucntion which handles the editing of messages.
        :param before: message before edit
        :param after: message after edit
        :return:
        """
        if before.content is not after.content:
            stored_message = self.message_manager.get_message(trigger_message_id=before.id)
            if stored_message is not None:
                pollmessage = stored_message.poll_message
                if self.is_multi_poll_command(after.content):
                    await self.delete_pollmessage(poll_message=pollmessage, trigger_message=after,
                                                  post_notification=False,stored_message=stored_message)
                    await self.process_commands(after)
                elif self.is_single_poll_command(after.content):
                    if self.is_multi_poll_command(before.content):
                        await self.delete_pollmessage(poll_message=pollmessage, trigger_message=after,
                                                      post_notification=False,stored_message=stored_message)
                        await self.create_single_poll(trigger_message=after, poll_title=after.content)
                    else:
                        # get poll
                        poll_id = self.message_manager.pollmessage_id_to_poll_id[pollmessage.id]
                        poll = self.poll_factory.polls[poll_id]
                        poll.poll_title = after.content
                        poll.create_summary_message()
                        await self.edit_message(pollmessage, poll.summary_message)
                else:
                    await self.delete_pollmessage(poll_message=pollmessage, trigger_message=after,
                                                  post_notification=True, stored_message=stored_message)
                self.storage_manager.update_storage(message_manager=self.message_manager,
                                                    poll_factory=self.poll_factory, client_messages=self.messages)

    async def update_poll_after_restart(self, pollmessage_id, reactions):
        """
        Function which is used to update polls after a restart of the bot,
        The function will read the reactions of a poll message and update the poll accordingly,
        this enables voting, even if the bot is offline.
        :param pollmessage_id: id of the pollmessage, which shall be updated
        :param reactions: reactions of the pollmessage.
        :return:
        """
        stored_message = self.message_manager.get_message(poll_message_id=pollmessage_id)
        if stored_message:
            # get poll
            poll_id = self.message_manager.pollmessage_id_to_poll_id[pollmessage_id]
            poll = self.poll_factory.polls[poll_id]
            # add reactions
            poll.reactions = []
            for reaction in reactions:
                users = await self.get_reaction_users(reaction)
                for user in users:
                    if self.user != user:
                        poll.reactions.append((reaction, user))
            # edit poll
            if isinstance(poll, MultiPoll):
                poll.update_embed()
                await self.edit_msg(stored_message.poll_message, poll.embed)
            elif isinstance(poll, SinglePoll):
                poll.create_summary_message()
                await self.edit_message(stored_message.poll_message, poll.summary_message)

    def is_multi_poll_command(self, message_content):
        """
        Function which checks whether a message is a command that triggers the creation of a MultiPoll object.
        :param message_content: content of a discord message (a string)
        :return:
        """
        poll_command = '%spoll' % self.command_prefix
        return message_content.startswith(poll_command)

    def is_single_poll_command(self, message_content):
        """
        Function which checks whether a message is a command that triggers the creation of a SinglePoll object.
        :param message_content: content of a discord message (a string)
        :return:
        """
        poll_command = 'raid '
        return message_content.lower().startswith(poll_command)

    async def on_message(self, message):
        """
        Function which handles posted messages by anyone.
        Used to check whether a message triggers the creation of a SinglePoll object.
        Falls back to the parent method of commands.Bot if not.
        :param message: posted message
        :return:
        """
        if message.content.lower().startswith("raid "):
            if message.author != self.user:
                await self.create_single_poll(trigger_message=message, poll_title=message.content)
        else:
            await super().on_message(message)

    @asyncio.coroutine
    def process_commands(self, message):
        """|coro|

        This function processes the commands that have been registered
        to the bot and other groups. Without this coroutine, none of the
        commands will be triggered.

        By default, this coroutine is called inside the :func:`on_message`
        event. If you choose to override the :func:`on_message` event, then
        you should invoke this coroutine as well.

        Warning
        --------
        This function is necessary for :meth:`say`, :meth:`whisper`,
        :meth:`type`, :meth:`reply`, and :meth:`upload` to work due to the
        way they are written. It is also required for the :func:`on_command`
        and :func:`on_command_completion` events.

        Parameters
        -----------
        message : discord.Message
            The message to process commands for.
        """
        message.content =  replace_quotes(message.content)
        _internal_channel = message.channel
        _internal_author = message.author

        view = StringView(message.content)
        if self._skip_check(message.author, self.user):
            return

        prefix = yield from self._get_prefix(message)
        invoked_prefix = prefix

        if not isinstance(prefix, (tuple, list)):
            if not view.skip_string(prefix):
                return
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return

        invoker = view.get_word()
        tmp = {
            'bot': self,
            'invoked_with': invoker,
            'message': message,
            'view': view,
            'prefix': invoked_prefix
        }
        ctx = Context(**tmp)
        del tmp

        if invoker in self.commands:
            command = self.commands[invoker]
            self.dispatch('command', command, ctx)
            try:
                yield from command.invoke(ctx)
            except CommandError as e:
                ctx.command.dispatch_error(e, ctx)
            else:
                self.dispatch('command_completion', command, ctx)
        elif invoker:
            exc = CommandNotFound('Command "{}" is not found'.format(invoker))
            self.dispatch('command_error', exc, ctx)

    async def edit_msg(self, message, embed):
        await self.edit_message(message, message.content, embed=embed)


    async def update_polls(self):
        outdated_messages = []
        LOGGER.info("Updating Polls.")
        self.message_manager.dump_and_remove(240.0)
        messages = copy.deepcopy(self.message_manager.messages)
        for message in messages.values():
            LOGGER.info("Updating poll %s" % message.trigger_message.content)
            # Check if triggermessage exists.
            trigger_message = await self.get_message_if_exists(channel=message.trigger_message.channel,
                                                               msg_id=message.trigger_message.id)
            # Check if poll exists.
            poll_message = await self.get_message_if_exists(channel=message.poll_message.channel,
                                                            msg_id=message.poll_message.id)
            # Case 1: triggermessage + poll exists. ---> Update polls.
            # Case 2: triggermessage exists, poll exists not. ---> process triggermessage, remove stored message
            # Case 3: triggermessage does not exist, poll exists. ---> delete poll, remove stored message.
            # Case 4: triggermessage + poll do not exist anymore ---> remove stored message,
            if trigger_message and poll_message:
                await self.update_poll_after_restart(poll_message.id, poll_message.reactions)
            elif trigger_message and poll_message is None:
                LOGGER.info("poll for trigger_message does not exist anymore,"
                            " processing trigger_message with content '%s'" % trigger_message.content)
                await self.process_commands(trigger_message)
                outdated_messages.append(message.id)
            elif trigger_message is None and poll_message:
                LOGGER.info("trigger_message with content '%s' does not exist anymore, "
                            "deleting poll." % message.trigger_message.content)
                await self.delete_pollmessage(poll_message=poll_message,
                                              trigger_message=message.trigger_message,
                                              post_notification=True,
                                              update_storage=True)
                outdated_messages.append(message.id)
            elif trigger_message is None and poll_message is None:
                LOGGER.info("trigger_message and poll do not exist anymore, deleting message.")
                outdated_messages.append(message.id)
        LOGGER.info("Polls Updated.")

        # delete outdated messages
        for message_id in outdated_messages:
            self.message_manager.delete_message(message_id=message_id)

    async def restore_messages_and_polls(self):
        self.storage_manager.load_storage()
        if self.storage_manager.storage is not None:
            # restore polls
            self.poll_factory.restore_polls(polls=self.storage_manager.storage.polls)

            # restore message_manager data
            message_storage = self.storage_manager.storage.message_storage
            self.message_manager.restore_messages(message_storage=message_storage)

            # restore old discord messages
            self.messages = self.storage_manager.storage.client_messages

            try:
                await self.update_polls()
            except RuntimeError as err:
                LOGGER.warning(err)
                # try again
                await self.update_polls()

            self.storage_manager.update_storage(message_manager=self.message_manager,
                                                poll_factory=self.poll_factory, client_messages=self.messages)

    async def get_message_if_exists(self, channel, msg_id):
        try:
            message = await self.get_message(channel=channel, id=msg_id)
            return message
        except discord.NotFound:
            return None

