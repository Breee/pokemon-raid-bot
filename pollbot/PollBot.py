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
from poll.emoji_storage import *
import discord
import datetime
import aiohttp
import logging

LOGGER = logging.getLogger('discord')
with open('help_msg.txt', 'r') as helpfile:
    HELP_MSG = helpfile.read()


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
        self.remove_command("help")
        self.add_command(self.help)
        self.start_time = 0
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def on_ready(self):
        LOGGER.info("Bot is ready.")
        self.start_time = datetime.datetime.utcnow()
        global PEOPLE_EMOJI_TO_NUMBER
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

            if number is not None:
                PEOPLE_EMOJI_TO_NUMBER[emoji] = number

        if len(PEOPLE_EMOJI_TO_NUMBER) != 4:
           PEOPLE_EMOJI_TO_NUMBER = dict()
           PEOPLE_EMOJI_TO_NUMBER = DEFAULT_PEOPLE_EMOJI_TO_NUMBER

        await self.change_presence(game=discord.Game(name=self.config.playing))
        await self.restore_messages_and_polls()

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

    @commands.command()
    async def help(self):
        await self.say(HELP_MSG)

    @commands.command(pass_context=True)
    async def poll(self, ctx, poll_title, *vote_options):
        await self.create_multi_poll(trigger_message=ctx.message, poll_title=poll_title, vote_options=vote_options)
        self.storage_manager.update_storage(message_manager=self.message_manager, poll_factory=self.poll_factory, client_messages=self.messages)

    async def create_multi_poll(self, trigger_message, poll_title, vote_options):
        """
        Function that creates a new MultiPoll and posts it.
        :param trigger_message: Message which triggered the creation of the poll
        :param poll_title: Title of the poll
        :param vote_options: List of string which contains vote options.
        :return:
        """
        # Create a new poll and post it.
        poll = self.poll_factory.create_multi_poll(poll_title=poll_title, vote_options=vote_options)
        poll_message = await self.send_message(trigger_message.channel,
                                               content="Poll for ***%s***" % (poll_title),
                                               embed=poll.embed)

        self.message_manager.create_message(trigger_message=trigger_message,
                                            poll_message=poll_message, poll_id=poll.poll_ID)

        # add vote emojies as reaction
        sorted_emoji = [(k, LETTEREMOJI_TO_NUMBER[k]) for k in sorted(LETTEREMOJI_TO_NUMBER, key=LETTEREMOJI_TO_NUMBER.get)]
        for emoji, n in sorted_emoji:
            if n <= len(vote_options) - 1:
                await self.add_reaction(poll_message, emoji)

        # add people emojie as reaction
        sorted_people_emoji = [(k, PEOPLE_EMOJI_TO_NUMBER[k]) for k in
                               sorted(PEOPLE_EMOJI_TO_NUMBER, key=PEOPLE_EMOJI_TO_NUMBER.get)]
        for emoji, n in sorted_people_emoji:
            await self.add_reaction(poll_message, emoji)

    async def create_single_poll(self, trigger_message, poll_title):
        """
        Function that creates a new Singlepoll and posts it.
        :param trigger_message: Message which triggered the creation of the poll
        :param poll_title: Title of the poll
        :return:
        """
        # Create a new poll and post it.
        poll = self.poll_factory.create_single_poll(poll_title=poll_title)
        poll.create_summary_message()
        poll_message = await self.send_message(trigger_message.channel,
                                               content=poll.summary_message)

        self.message_manager.create_message(trigger_message=trigger_message,
                                            poll_message=poll_message, poll_id=poll.poll_ID)

        # add people emojie as reaction
        sorted_people_emoji = [(k, EMOJI_TO_NUMBER[k]) for k in
                               sorted(EMOJI_TO_NUMBER, key=EMOJI_TO_NUMBER.get)]
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
            # reaction has to be part of the vote emojis/ people emojis
            if reaction.emoji in LETTEREMOJI_TO_NUMBER or reaction.emoji in PEOPLE_EMOJI_TO_NUMBER or reaction.emoji in EMOJI_TO_NUMBER:
                stored_message = self.message_manager.get_message(poll_message_id=reaction.message.id)
                if stored_message:
                    # get poll
                    poll_id =  self.message_manager.pollmessage_id_to_poll_id[reaction.message.id]
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
            if reaction.emoji in LETTEREMOJI_TO_NUMBER or reaction.emoji in PEOPLE_EMOJI_TO_NUMBER or reaction.emoji in EMOJI_TO_NUMBER:
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
                                              trigger_message=stored_message.trigger_message)
                # remove the message
                self.message_manager.delete_message(stored_message.id)
                self.storage_manager.update_storage(message_manager=self.message_manager, poll_factory=self.poll_factory,
                                                    client_messages=self.messages)

    async def delete_pollmessage(self, poll_message, trigger_message, post_notification=True):
        """
        Fucntion which deletes a pollmessage
        :param poll_message: message which contains the poll.
        :param trigger_message: message which triggered the creation of the poll.
        :param post_notification: Boolean which determines whether a notification about the deletion gets posted or not.
        :return:

        """
        # get poll
        poll_id = self.message_manager.pollmessage_id_to_poll_id[poll_message.id]
        # add reactions
        poll = self.poll_factory.polls[poll_id]
        await self.delete_message(poll_message)
        if post_notification:
            await self.send_message(trigger_message.channel, content="Deleted poll #%s: %s" % (poll.poll_ID, poll.poll_title))

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
                                                  post_notification=False)
                    await self.process_commands(after)
                elif self.is_single_poll_command(after.content):
                    if self.is_multi_poll_command(before.content):
                        await self.delete_pollmessage(poll_message=pollmessage, trigger_message=after,
                                                      post_notification=False)
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
                                                  post_notification=True)
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

            LOGGER.info("Updating Polls.")

            for message in self.message_manager.messages.values():
                current_state = await self.get_message(message.poll_message.channel, message.poll_message.id)
                await self.update_poll_after_restart(current_state.id, current_state.reactions)

            LOGGER.info("Polls Updated.")
            self.storage_manager.update_storage(message_manager=self.message_manager,
                                                poll_factory=self.poll_factory, client_messages=self.messages)


