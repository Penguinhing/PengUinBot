

import os
from discord.ext import commands
from lib.sql.data import Query


class Owner(commands.Cog):

    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.query = Query()
    
    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx : commands.Context):
        for extenison in os.listdir('lib/cogs'):
            if extenison[-3:] == '.py' and extenison.find('owner') == -1:
                await self.bot.reload_extension('lib.cogs.' + extenison[:-3])
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send("reloaded")



async def setup(bot):
    await bot.add_cog(Owner(bot))