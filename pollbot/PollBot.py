from config.Configuration import Configuration
from messages.MessageManager import MessageManager
from poll.PollFactory import PollFactory
from discord.ext import commands
from utils import replace_quotes
from poll.emoji_storage import *
import discord
import datetime
import aiohttp


class PollBot(commands.Bot):
    def __init__(self, prefix, description, config_file):
        super().__init__(command_prefix=prefix, description=description, pm_help=None, help_attrs=dict(hidden=True))
        self.config = Configuration(config_file)
        self.poll_factory = PollFactory()
        self.message_manager = MessageManager()
        self.add_command(self.ping)
        self.add_command(self.poll)
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def on_ready(self):
        self.up_time = datetime.datetime.utcnow()
        print(self.up_time)

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

    @commands.command(pass_context=True)
    async def poll(self, ctx, poll_title, *vote_options):
        # dirty hacks TODO: remove asap and find a proper solution.
        if '„' in ctx.message.content and '“' in ctx.message.content:
            poll_title, vote_options = self.preprocess_poll_command(ctx.message.content)
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
        sorted_emoji = [(k, EMOJI_TO_NUMBER[k]) for k in sorted(EMOJI_TO_NUMBER, key=EMOJI_TO_NUMBER.get)]
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
            # reaction has to be part of the vote emojies/ people emojies
            if reaction.emoji in EMOJI_TO_NUMBER or reaction.emoji in PEOPLE_EMOJI_TO_NUMBER:
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
            if reaction.emoji in EMOJI_TO_NUMBER or reaction.emoji in PEOPLE_EMOJI_TO_NUMBER:
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
                    if '„' in after.content and '“' in after.content:
                        poll_title, vote_options = self.preprocess_poll_command(after.content)
                    else:
                        # rebuild args
                        cmd = after.content.replace('!raid-poll ', '').split(' ')
                        poll_title = cmd[0].strip()
                        vote_options = cmd[1:]
                    await self.delete_pollmessage(pollmessage=pollmessage, triggermessage=after, post_notification=False)
                    await self.create_poll(trigger_message=after, poll_title=poll_title, vote_options=vote_options)
                else:
                    await self.delete_pollmessage(pollmessage=pollmessage, triggermessage=after, post_notification=True)


    def is_poll_command(self, message_content):
        poll_command = '%spoll' % self.command_prefix
        return message_content.startswith(poll_command)

    def preprocess_poll_command(self, command):
        #TODO: HACK!
        # replace stupid quotes
        command = replace_quotes(command)
        # rebuild args
        cmd = command.replace('!raid-poll ', '').split('$$$')
        poll_title = cmd[0].replace('"', '')
        vote_options = cmd[1].strip().split(" ")
        return poll_title, vote_options


    async def edit_msg(self, message, embed):
        await self.edit_message(message, message.content, embed=embed)