import discord, os
from discord.ext import commands, tasks
from view.setting import *


bot = commands.Bot(command_prefix="-", help_command=None, intents=discord.Intents.all())


@bot.event
async def on_guild_join(guild): # 봇이 새로운 서버에 입장한 경우 설정 적용
    music = bot.get_cog('노래')
    voice = bot.get_cog('통화')
    music.playlist[guild.id] = []
    music.config[guild.id] = {'loop':False}
    voice.config[guild.id] = {'notice':True}


@bot.event
async def setup_hook():
    await bot.load_extension('data.mysql')
    for extenison in os.listdir('cogs'):
        if extenison[-3:] == '.py':
            await bot.load_extension('cogs.' + extenison[:-3])
    await bot.tree.sync()


@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    await bot.change_presence(activity=discord.Game(name=f"{len(bot.guilds)}개의 서버에서 사용"))
    auto_reload_mysql.start()

@bot.event
async def on_command_error(ctx, error):
    print(error)
    if isinstance(error, commands.ArgumentParsingError):
        await ctx.send(embed = discord.Embed(description="올바른 값을 입력해주세요.\n", color = color['red']).set_author(name="ERROR", icon_url=icon['error']))




########################################################################################################################
########################################################################################################################

@tasks.loop(hours=6) # mysql 오류 방지
async def auto_reload_mysql(self):
    await reload_helper()

async def reload_helper():
    voice_time = bot.get_cog('통화').voice_time
    await bot.reload_extension('data.mysql')
    for extenison in os.listdir('cogs'):
        if extenison[-3:] == '.py':
            await bot.reload_extension('cogs.' + extenison[:-3])
    bot.get_cog('통화').voice_time = voice_time


@bot.command()
@commands.is_owner()
async def reload(ctx):
    await reload_helper()
    await ctx.send('reloaded')


bot.run('token')