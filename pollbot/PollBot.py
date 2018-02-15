from config.Configuration import Configuration
from discord.ext import commands
import discord
import datetime
import aiohttp

class PollBot(commands.Bot):
    def __init__(self, prefix, description, config_file):
        super().__init__(command_prefix=prefix, description=description, pm_help=None, help_attrs=dict(hidden=True))
        self.config = Configuration(config_file)
        self.add_command(self.ping)
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def on_ready(self):
        self.up_time = datetime.datetime.utcnow()
        print(self.up_time)

    def run(self):
        super().run(self.config.token)

    async def close(self):
        await super().close()
        await self.session.close()
        await super().logout()

    async def on_resumed(self):
        print('resumed...')

    @commands.command(hidden=True)
    async def ping(self):
        await self.say("pong!")
