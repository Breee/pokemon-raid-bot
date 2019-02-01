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
from poll.PollFactory import PollFactory
from poll.MultiPoll import MultiPoll
from poll.SinglePoll import SinglePoll
from discord.ext import commands
from utils import replace_quotes
from poll.emoji_storage import EmojiStorage
import discord
import datetime
import aiohttp
import os
from globals.globals import LOGGER
from database.dbhandler import DbHandler
from database.dbmodels import Poll
import asyncio
import sys
import traceback

if os.path.isfile('help_msg.txt'):
    with open('help_msg.txt', 'r') as helpfile:
        HELP_MSG = helpfile.read()

BANNED_USERS = []
if os.path.isfile('banned_users.txt'):
    with open('banned_users.txt', 'r') as banned_users:
        for line in banned_users:
            BANNED_USERS.append(line)

class PollBot(commands.Bot):
    def __init__(self, prefixes, description, config_file):
        super().__init__(command_prefix=prefixes, description=description, pm_help=None, help_attrs=dict(hidden=True), fetch_offline_members=False, case_insensitive=True)
        self.config = Configuration(config_file)
        self.poll_factory = PollFactory()
        self.add_command(self.ping)
        self.add_command(self.poll)
        self.add_command(self.uptime)
        self.add_command(self.readpoll)
        self.add_command(self.update)
        self.add_command(self.ready)
        self.start_time = 0.0
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.use_custom_emojies = True
        self.db_handler = DbHandler(host=self.config.db_host, user=self.config.db_user, password=self.config.db_password,
                                    port=self.config.db_port, database=self.config.db_name, dialect=self.config.db_dialect, driver=self.config.db_driver)
        self.ready = False

    async def on_ready(self):
        LOGGER.info("Bot initializing")
        # make mentionable.
        self.command_prefix.extend([f'<@!{self.user.id}> ', f'<@{self.user.id}> '])
        self.start_time = datetime.datetime.utcnow()
        await self.init_custom_emojies()
        self.ready = False
        LOGGER.info("Restoring messages")
        await self.restore_messages_and_polls(days=1)
        self.ready = True
        LOGGER.info("Bot ready")


    async def init_custom_emojies(self):
        LOGGER.info("Init custom emojies")
        if self.use_custom_emojies:
            EmojiStorage.PEOPLE_EMOJI_TO_NUMBER = dict()
            if self.use_custom_emojies:
                EmojiStorage.PEOPLE_EMOJI_TO_NUMBER = dict()
                server_emojis = self.emojis
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
        LOGGER.info("Closing")

    @commands.command(help="Pings the Bot.")
    async def ping(self, ctx):
        await ctx.send("pong!, ready: %s" % self.ready)

    @commands.command(help="Ready the Bot.", hidden=True)
    @commands.is_owner()
    async def ready(self, ctx):
        self.ready = not self.ready
        await ctx.send("ready: %s" % self.ready)

    @commands.command(hidden=True)
    async def uptime(self, ctx):
        await ctx.send("Online for %s" % str(datetime.datetime.utcnow() - self.start_time))

    @commands.command()
    async def help(self, ctx, here=None):
        await ctx.send(HELP_MSG)

    @commands.command()
    async def update(self, ctx, days):
        self.ready = False
        await ctx.send("Updating polls...")
        await self.restore_messages_and_polls(days)
        await ctx.send("Ready!")
        self.ready = True

    @commands.command(help="Creates a poll.\n"
                           "Usage:\n"
                           "   <prefix> \"<poll_title>\" <option_1> <option_2> ... \n"
                           "Example:\n"
                           "   <prefix> \"Rayquaza Jump & Twist\" 9:00 9:15 9:30 9:40")
    async def poll(self, ctx, poll_title, *vote_options):
        if str(ctx.message.author) in BANNED_USERS:
            LOGGER.warning("Denied creation of poll, User %s is banned" % ctx.message.author)
            return
        with ctx.typing():
            await self.create_multi_poll(ctx=ctx, trigger_message=ctx.message, poll_title=poll_title, vote_options=vote_options)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def readpoll(self, ctx, trigger_id, msg_id, *vote_options):
        msg = await self.get_message_if_exists(channel_id=ctx.channel.id,message_id=msg_id)
        trigger = await self.get_message_if_exists(channel_id=ctx.channel.id, message_id=trigger_id)
        title = msg.content.replace("Poll for", "")
        poll = self.poll_factory.create_multi_poll(poll_title=title, vote_options=vote_options)
        poll.update_embed()
        self.db_handler.add_poll(poll, trigger, msg)
        self.db_handler.update_poll(poll)

        await msg.edit(content=msg.content, embed=poll.embed)
        await self.update_poll_after_restart(msg_id,msg.reactions)

    async def create_multi_poll(self, ctx, trigger_message, poll_title, vote_options):
        """
        Function that creates a new MultiPoll and posts it.
        :param trigger_message: Message which triggered the creation of the poll
        :param poll_title: Title of the poll
        :param vote_options: List of string which contains vote options.
        :return:
        """
        LOGGER.info("Creating Multipoll: "
                    "trigger_message: %s,"
                    "poll_title: %s,"
                    "vote_options: %s" % (trigger_message.content, poll_title, vote_options))
        # Create a new poll and post it.
        poll = self.poll_factory.create_multi_poll(poll_title=poll_title, vote_options=vote_options)
        poll_message = await ctx.send(content="Poll for **%s**" % (poll_title),embed=poll.embed)
        self.db_handler.add_poll(poll, trigger_message, poll_message)

        # add vote emoji as reaction
        sorted_emoji = [(k, EmojiStorage.LETTEREMOJI_TO_NUMBER[k]) for k in sorted(EmojiStorage.LETTEREMOJI_TO_NUMBER, key=EmojiStorage.LETTEREMOJI_TO_NUMBER.get)]
        for emoji, n in sorted_emoji:
            if n <= len(vote_options) - 1:
                await poll_message.add_reaction(emoji)

        # add people emoji as reaction
        sorted_people_emoji = [(k, EmojiStorage.PEOPLE_EMOJI_TO_NUMBER[k]) for k in
                               sorted(EmojiStorage.PEOPLE_EMOJI_TO_NUMBER, key=EmojiStorage.PEOPLE_EMOJI_TO_NUMBER.get)]
        for emoji, n in sorted_people_emoji:
            await poll_message.add_reaction(emoji)

    async def create_single_poll(self,trigger_message, poll_title):
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
        poll_message = await trigger_message.channel.send(content=poll.summary_message)
        self.db_handler.add_poll(poll, trigger_message, poll_message)

        # add people emojie as reaction
        sorted_people_emoji = [(k, EmojiStorage.EMOJI_TO_NUMBER[k]) for k in
                               sorted(EmojiStorage.EMOJI_TO_NUMBER, key=EmojiStorage.EMOJI_TO_NUMBER.get)]
        for emoji, n in sorted_people_emoji:
            if n < 4:
                await poll_message.add_reaction(emoji)

    async def on_raw_reaction_add(self, ctx):
        if not self.ready:
            return
        data = {'count' : 1, 'me': ctx.user_id == self.user.id, 'emoji' : {'id': ctx.emoji.id, 'name': ctx.emoji.name}}
        channel = self.get_channel(ctx.channel_id)
        message = await channel.get_message(ctx.message_id)
        reaction = discord.Reaction(message=message, data=data)
        user = self.get_user(ctx.user_id)
        if user != self.user:
            # reaction has to be part of the vote emojis/ people emojis
            if reaction.emoji in EmojiStorage.LETTEREMOJI_TO_NUMBER or EmojiStorage.is_people_emoji(reaction.emoji) or reaction.emoji in EmojiStorage.EMOJI_TO_NUMBER:
                # get poll
                poll_db = self.db_handler.get_poll_with_message_id(message_id=reaction.message.id)
                # add reactions
                if poll_db:
                    poll = self.poll_factory.polls[poll_db.external_id]
                    poll.reactions.append((reaction, user))
                    # edit poll
                    if isinstance(poll, MultiPoll):
                        poll.update_embed()
                        await reaction.message.edit(content=reaction.message.content, embed=poll.embed)
                    elif isinstance(poll, SinglePoll):
                        poll.create_summary_message()
                        await reaction.message.edit(content=poll.summary_message)
                    # update poll in DB
                    self.db_handler.update_poll(poll)

    async def on_raw_reaction_remove(self, ctx):
        if not self.ready:
            return
        data = {'count' : 1, 'me': ctx.user_id == self.user.id, 'emoji' : {'id': ctx.emoji.id, 'name': ctx.emoji.name}}
        channel = self.get_channel(ctx.channel_id)
        message = await channel.get_message(ctx.message_id)
        reaction = discord.Reaction(message=message, data=data)
        user = self.get_user(ctx.user_id)
        if user != self.user:
            if reaction.emoji in EmojiStorage.LETTEREMOJI_TO_NUMBER or EmojiStorage.is_people_emoji(
                    reaction.emoji) or reaction.emoji in EmojiStorage.EMOJI_TO_NUMBER:
                poll_db = self.db_handler.get_poll_with_message_id(message_id=reaction.message.id)
                if poll_db:
                    # add reactions
                    poll = self.poll_factory.polls[poll_db.external_id]
                    poll.reactions.remove((reaction, user))
                    # edit poll
                    if isinstance(poll, MultiPoll):
                        poll.update_embed()
                        await reaction.message.edit(content=reaction.message.content, embed=poll.embed)
                    elif isinstance(poll, SinglePoll):
                        poll.create_summary_message()
                        await reaction.message.edit(content=poll.summary_message)
                    # update poll in DB
                    self.db_handler.update_poll(poll)


    async def on_raw_message_delete(self, message : discord.raw_models.RawMessageDeleteEvent):
        """
        Function which handles messages that have been deleted.
        :param message: deleted message.
        :return:
        """
        if isinstance(message, discord.raw_models.RawMessageDeleteEvent):
            poll = self.db_handler.disable_poll_via_id(message_id=message.message_id)
            if poll:
                message = await self.get_message_if_exists(poll.channel, poll.poll_message)
                if message:
                    await message.delete()

    async def update_poll_after_restart(self, pollmessage_id, reactions):
        """
        Function which is used to update polls after a restart of the bot,
        The function will read the reactions of a poll message and update the poll accordingly,
        this enables voting, even if the bot is offline.
        :param pollmessage_id: id of the pollmessage, which shall be updated
        :param reactions: reactions of the pollmessage.
        :return:
        """
        # get poll
        poll_model = self.db_handler.get_poll_with_message_id(pollmessage_id)
        if poll_model:
            poll_message = await self.get_message_if_exists(channel_id=poll_model.channel, message_id=poll_model.poll_message)
            poll = self.poll_factory.polls[poll_model.external_id]
            # add reactions
            poll.reactions = []
            for reaction in reactions:
                users = reaction.users()
                async for user in users:
                    if self.user != user:
                        poll.reactions.append((reaction, user))
            # edit poll
            if isinstance(poll, MultiPoll):
                poll.update_embed()
                await poll_message.edit(content=poll_message.content, embed=poll.embed)
            elif isinstance(poll, SinglePoll):
                poll.create_summary_message()
                await poll_message.edit(content=poll.summary_message)
            self.db_handler.update_poll(poll)

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

    async def on_message(self,message):
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
    async def process_commands(self, message):
        """|coro|

        This function processes the commands that have been registered
        to the bot and other groups. Without this coroutine, none of the
        commands will be triggered.

        By default, this coroutine is called inside the :func:`.on_message`
        event. If you choose to override the :func:`.on_message` event, then
        you should invoke this coroutine as well.

        This is built using other low level tools, and is equivalent to a
        call to :meth:`~.Bot.get_context` followed by a call to :meth:`~.Bot.invoke`.

        This also checks if the message's author is a bot and doesn't
        call :meth:`~.Bot.get_context` or :meth:`~.Bot.invoke` if so.

        Parameters
        -----------
        message: :class:`discord.Message`
            The message to process commands for.
        """
        if message.author.bot:
            return
        message.content = replace_quotes(message.content)
        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def update_polls(self, days=1):
        LOGGER.info("Updating Polls of the last %d day(s)" % days)
        # get enabled polls
        polls = self.db_handler.get_polls(age=days)
        for poll in polls:
            try:
                LOGGER.info("Updating poll %s" % poll.external_id)
                # Check if triggermessage exists.
                trigger_message = await self.get_message_if_exists(channel_id=poll.channel,
                                                                   message_id=poll.trigger_message)
                # Check if poll exists.
                poll_message = await self.get_message_if_exists(channel_id=poll.channel,
                                                                message_id=poll.poll_message)
                # Case 1: triggermessage + poll exists. ---> Update polls.
                # Case 2: triggermessage exists, poll exists not.
                # Case 3: triggermessage does not exist, poll exists.
                # Case 4: triggermessage + poll do not exist anymore
                if trigger_message and poll_message:
                    await self.update_poll_after_restart(poll_message.id, poll_message.reactions)
                elif trigger_message is None and poll_message:
                    LOGGER.debug("trigger_message does not exist anymore")
                    await poll_message.delete()
                    self.db_handler.disable_poll_via_id(poll_message.id)
                elif trigger_message is None and poll_message is None:
                    LOGGER.debug("trigger_message and poll do not exist anymore")
            except Exception as err:
                LOGGER.critical("Error. %s" % err)
        LOGGER.info("Polls Updated.")

    async def restore_messages_and_polls(self, days):
        polls = self.db_handler.get_polls()
        self.poll_factory.restore_polls(polls=polls)
        await self.update_polls(days)

    async def get_message_if_exists(self, channel_id, message_id):
        try:
            channel = self.get_channel(int(channel_id))
            if channel:
                message = await channel.get_message(message_id)
                return message
        except discord.NotFound:
            return None

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.CommandInvokeError):
            print(f'In {ctx.command.qualified_name}:', file=sys.stderr)
            traceback.print_tb(error.original.__traceback__)
            print(f'{error.original.__class__.__name__}: {error.original}', file=sys.stderr)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.author.send('Sorry. This command is not how this command works.\n %s' % HELP_MSG)
