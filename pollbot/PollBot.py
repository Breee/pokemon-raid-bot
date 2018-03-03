from config.Configuration import Configuration
from messages.MessageManager import MessageManager
from poll.PollFactory import PollFactory
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

logger = logging.getLogger('discord')

class PollBot(commands.Bot):
    def __init__(self, prefix, description, config_file):
        super().__init__(command_prefix=prefix, description=description, pm_help=None, help_attrs=dict(hidden=True))
        self.config = Configuration(config_file)
        self.poll_factory = PollFactory()
        self.message_manager = MessageManager()
        self.add_command(self.ping)
        self.add_command(self.poll)
        self.add_command(self.uptime)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.start_time = 0

    async def on_ready(self):
        logger.info("Bot is ready.")
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

    def run(self):
        super().run(self.config.token)

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
    async def poll(self, ctx, poll_title, *vote_options):
        await self.create_poll(trigger_message=ctx.message, poll_title=poll_title, vote_options=vote_options)

    async def create_poll(self, trigger_message, poll_title, vote_options):
        """
        Function that creates a new poll and posts it.
        :param trigger_message: Message which triggered the creation of the poll
        :param poll_title: Title of the poll
        :param vote_options: List of string which contains vote options.
        :return:
        """
        # Create a new poll and post it.
        poll = self.poll_factory.create_poll(poll_title=poll_title, vote_options=vote_options)
        poll_message = await self.send_message(trigger_message.channel,
                                          content="Created poll #%s.\n%s" % (poll.poll_ID, poll_title),
                                          embed=poll.embed)

        self.message_manager.create_message(trigger_message=trigger_message, poll_message=poll_message, poll_id=poll.poll_ID)

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

    async def on_reaction_add(self, reaction, user):
        if user != self.user:
            # reaction has to be part of the vote emojis/ people emojis
            if reaction.emoji in LETTEREMOJI_TO_NUMBER or reaction.emoji in PEOPLE_EMOJI_TO_NUMBER:
                if reaction.message.id in self.message_manager.pollmessage_id_to_pollmessage:
                    # get poll
                    poll_id =  self.message_manager.pollmessage_id_to_poll_id[reaction.message.id]
                    # add reactions
                    poll = self.poll_factory.polls[poll_id]
                    poll.reactions.append((reaction, user))
                    # edit poll
                    poll.update_embed()
                    # edit message
                    await self.edit_msg(reaction.message, poll.embed)

    async def on_reaction_remove(self, reaction, user):
        if user != self.user:
            if reaction.emoji in LETTEREMOJI_TO_NUMBER or reaction.emoji in PEOPLE_EMOJI_TO_NUMBER:
                if reaction.message.id in self.message_manager.pollmessage_id_to_pollmessage:
                    # get poll
                    poll_id =  self.message_manager.pollmessage_id_to_poll_id[reaction.message.id]
                    # add reactions
                    poll = self.poll_factory.polls[poll_id]
                    poll.reactions.remove((reaction, user))
                    # edit poll
                    poll.update_embed()
                    # edit message
                    await self.edit_msg(reaction.message, poll.embed)

    async def on_message_delete(self, message):
        if isinstance(message, discord.Message):
            if message.id in self.message_manager.triggermessage_id_to_pollmessage:
                pollmessage = self.message_manager.triggermessage_id_to_pollmessage[message.id]
                await self.delete_pollmessage(pollmessage=pollmessage, triggermessage=message)

    async def delete_pollmessage(self, pollmessage, triggermessage, post_notification=True):
        """
        Fucntion which deletes a pollmessage
        :param pollmessage: message which contains the poll.
        :param triggermessage: message which triggered the creation of the poll.
        :param post_notification: Boolean which determines whether a notification about the deletion gets posted or not.
        :return:

        """
        # get poll
        poll_id = self.message_manager.pollmessage_id_to_poll_id[pollmessage.id]
        # add reactions
        poll = self.poll_factory.polls[poll_id]
        await self.delete_message(pollmessage)
        if post_notification:
            await self.send_message(triggermessage.channel, content="Deleted poll #%s: %s" % (poll.poll_ID, poll.poll_title))

    async def on_message_edit(self, before, after):
        if before.content is not after.content:
            if before.id in self.message_manager.triggermessage_id_to_pollmessage:
                pollmessage = self.message_manager.triggermessage_id_to_pollmessage[before.id]
                if self.is_poll_command(after.content):
                    await self.delete_pollmessage(pollmessage=pollmessage, triggermessage=after, post_notification=False)
                    await self.process_commands(after)
                else:
                    await self.delete_pollmessage(pollmessage=pollmessage, triggermessage=after, post_notification=True)


    def is_poll_command(self, message_content):
        poll_command = '%spoll' % self.command_prefix
        return message_content.startswith(poll_command)

    def preprocess_poll_command(self, command):
        # replace stupid quotes
        command = replace_quotes(command)
        view = StringView(command)
        print(view)
        # rebuild args
        cmd = command.replace('!raid-poll ', '').split(' ')
        poll_title = cmd[0].replace('"', '')
        vote_options = cmd[1:len(command)]
        return poll_title, vote_options


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