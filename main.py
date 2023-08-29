import discord, os
import wavelink
from discord.ext import commands


class Bot(commands.Bot):

    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all(), command_prefix='.', help_command=None)

    async def on_ready(self) -> None:
        print(f'Logged in {self.user} | {self.user.id}')

    async def setup_hook(self) -> None:
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='your lavalink password')
        await wavelink.NodePool.connect(client=self, nodes=[node])
        for extenison in os.listdir('lib/cogs'):
            if extenison[-3:] == '.py':
                await bot.load_extension('lib.cogs.' + extenison[:-3])
        await bot.tree.sync()

bot = Bot()
bot.run('input your token')