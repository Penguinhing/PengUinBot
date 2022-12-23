
import discord, time, datetime as dt
from discord.ext import commands, tasks
from discord import app_commands
from view.setting import *


class VoiceCog(commands.Cog, name="통화"):

    def __init__(self, bot):
        self.bot = bot
        self.mysql = self.bot.get_cog('mysql')
        self.level = self.bot.get_cog('LV')
        self.voice_time = {} # 멤버별 통화 시작 시간 기록
        self.config = {} # 통화방 입퇴장 알림 설정
        for guild in self.bot.guilds:
            self.config[guild.id] = {'notice':True}
    


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
            if after.channel == before.channel:
                return
            # print(f'[LOG][{dt.datetime.utcnow() + dt.timedelta(hours=9)}] {member.name}#{member.discriminator} : {before} → {after}')

            if (after.channel != None and before.channel != None) or after.channel == None: # 통화방 퇴장 or 이동
                if self.voice_time[member.id]:
                    seconds = int(time.time() - self.voice_time[member.id]) # 통화시간 초단위
                    self.voice_time[member.id] = 0

                    if self.config[member.guild.id]['notice']: # 퇴장 알림
                        await before.channel.send(embed=discord.Embed(description=f":no_entry: ``{member}`` 님이 ``{before.channel.name}`` 채널에서 퇴장하셨습니다.", color=color['red'])\
                                .set_footer(text=f"총 통화 시간 {dt.timedelta(seconds=seconds)}"))

                    if seconds > 5 and not member.bot: # 통화시간이 5초 이상인 경우 저장
                        UUID = self.level.get_UUID(member.guild.id, member.id)
                        await self.mysql._execute(f"INSERT INTO user_info (SERVER_ID, MEMBER_ID, UUID, VOICE_TIME) VALUES ('{member.guild.id}','{member.id}', '{UUID}', {seconds}) ON DUPLICATE KEY UPDATE VOICE_TIME = VOICE_TIME+{seconds}")
                        await self.level.give_exp(UUID, EXP=seconds, member=member)


                else:
                    return await before.channel.send(f'{member.mention} 님, 통화 시간을 저장하는 데에 알 수 없는 오류가 발생하였습니다. 해당 통화 시간을 저장하시려면 개발자에게 문의해주세요.')
                

            
            if after.channel != None: # 채널 입장
                self.voice_time[member.id] = time.time()
                if self.config[member.guild.id]['notice']:
                    await after.channel.send(embed=discord.Embed(description=f":bell: ``{member}`` 님이 ``{after.channel.name}`` 채널에 입장하셨습니다.", color=color['green']))



    @app_commands.command(name="입퇴장", description="음성 채널의 입퇴장 알림 기능을 ON/OFF 합니다. (관리자 전용)")
    @app_commands.checks.has_permissions(administrator=True)
    async def notice(self, interaction:discord.Interaction):
        self.config[interaction.user.guild.id]['notice'] = not self.config[interaction.user.guild.id]['notice']
        await interaction.response.send_message("음성 채널의 입퇴장 알림을 {}습니다.".format('켰' if self.config[interaction.user.guild.id]['notice'] else '껐'), ephemeral=True)

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))