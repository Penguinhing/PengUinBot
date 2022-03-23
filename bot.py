import discord, os
from discord.ext import commands
from client.module.Setting import *

intent = discord.Intents.default()
intent.message_content = True
bot = commands.Bot(command_prefix="-", help_command=None, intents=intent)


@bot.command()
async def reload(ctx):
    for extenison in os.listdir('client/cogs'):
        if extenison[-3:] == '.py':
            await bot.reload_extension('client.cogs.' + extenison[:-3])
    await ctx.send("리로드 완료")

@bot.command(name="도움말", aliases=['help'])
async def help_command(ctx, func=None):
    cog_list = list(bot.cogs.keys())

    if func is None: # 일반 도움말
        embed = discord.Embed(title="", description="각 명령어에 대한 자세한 설명은 ``-도움말 [명령어]`` 를 입력해주세요.", color=color['blue'])
        embed.set_author(name="명령어 가이드", icon_url=icon['help'])

        # 명령어 목록 가져오기
        for x in cog_list:
            command_list = bot.get_cog(x).get_commands()
            embed.add_field(name=x + ' 명령어', value=" ".join(['``' + c.name + '``' for c in command_list]), inline=False)
        
        await ctx.send(embed=embed)

    else: # 상세 도움말
        command_notfound = True
        for cog in bot.cogs.values():
            if not command_notfound:
                return
            for title in cog.get_commands():
                if title.name == func:
                    cmd = bot.get_command(title.name)
                    embed = discord.Embed(title=f"[ {cmd} ]", description=cmd.help, color=color['green'])
                    embed.set_author(name="상세 가이드", icon_url=icon['info'])
                    embed.add_field(name="사용 방법", value=cmd.usage, inline=False)

                    if not cmd.aliases:
                        _aliases = 'X'
                    else:
                        _aliases = "\n".join(['-'+ x for x in cmd.aliases])

                    embed.add_field(name="그 외 명령어", value=_aliases, inline=False)
                    await ctx.send(embed=embed)
                    command_notfound = False
                    break
            
        if command_notfound: # 카테고리
            if func in cog_list:
                cog_data = bot.get_cog(func); command_list = cog_data.get_commands()
                embed = discord.Embed(title=f"[ {cog_data.qualified_name} ]", description=f"{func} 관련 모든 명령어를 불러왔습니다.", color=color['green'])
                embed.set_author(name="카테고리 명령어", icon_url=icon['info'])
                embed.add_field(name="- 명령어 목록", value=" ".join(['``' + c.name + '``' for c in command_list]))
                await ctx.send(embed=embed)
            else:
                raise commands.ArgumentParsingError


@bot.event
async def on_ready():
    for extenison in os.listdir('client/cogs'):
        if extenison[-3:] == '.py':
            await bot.load_extension('client.cogs.' + extenison[:-3])
    print("We have logged in as {0.user}".format(bot))
    await bot.change_presence(activity=discord.Game(name="제작: 명범"))

@bot.event
async def on_command_error(ctx, error):
    print(error)
    if isinstance(error, commands.CommandNotFound) or isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed = discord.Embed(description="올바른 명령어를 입력해주세요.\n", color = color['red']).set_author(name="명령어 오류", icon_url=icon['error']))

    if isinstance(error, commands.ArgumentParsingError):
        await ctx.send(embed = discord.Embed(description="제대로된 값을 입력해주세요.\n", color = color['red']).set_author(name="입력값 오류", icon_url=icon['error']))

bot.run('your token')