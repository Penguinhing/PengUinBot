from discord.ext import commands
from client.module.Setting import *
import discord

class WordchainCommand(commands.Cog, name="끝말잇기"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="단어검색", help="글자로 시작하는 단어 정보를 출력합니다.", usage="-단어검색 ``[글자]``")
    async def search_word(self, ctx, character):
        if len(character) != 1: raise commands.ArgumentParsingError

        wordbase = {'Fin':[], 'Attack':[], 'Defense':[]}

        for arg in wordbase.keys():
            with open(f'data/wordchain/{arg}.txt', 'r', encoding='utf-8') as FILE:
                for word in FILE.readlines():
                    if word.startswith(character):
                        wordbase[arg] += ['``' + word.rstrip('\n') + '``\n']
        embed = discord.Embed(title=f"'{character}' (으)로 시작하는 단어를 검색하였습니다.", color=color['blue'])
        embed.add_field(name="[바로 끝낼 수 있는 단어]", value=''.join(wordbase['Fin'] if len(wordbase['Fin']) > 0 else '검색된 결과가 없습니다.'), inline=False)
        embed.add_field(name="[고문하다가 끝내는 단어]", value=''.join(wordbase['Attack'] if len(wordbase['Attack']) > 0 else '검색된 결과가 없습니다.'), inline=False)
        embed.add_field(name="[방어 단어]", value=''.join(wordbase['Defense'] if len(wordbase['Defense']) > 0 else '검색된 결과가 없습니다.'), inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WordchainCommand(bot))