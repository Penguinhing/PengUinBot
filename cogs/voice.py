
import discord, time, datetime as dt
from discord.ext import commands, tasks
from discord import app_commands
from view.setting import *


class VoiceCog(commands.Cog, name="통화"):

    def __init__(self, bot):
        self.bot = bot
        self.voice_time = {} # 멤버별 통화 시간 기록
        self.config = {}
        for guild in self.bot.guilds:
            self.config[guild.id] = {'notice':True}
        
        self.auto_reload_mysql.start()



    @tasks.loop(hours=6) # mysql 오류 방지
    async def auto_reload_mysql(self):
        await self.bot.reload_extension('data.mysql')
        self.mysql = self.bot.get_cog('mysql')

        for guild in self.bot.guilds: # 랭커 업데이트
            ranker_role = await self.mysql.fetch_one_data(f"SELECT ROLE_ID FROM voice_ranker WHERE SERVER_ID = {guild.id}")
            users = await self.mysql.fetch_all_data(f"SELECT MEMBER_ID, TIME FROM voice_time WHERE SERVER_ID = {guild.id} ORDER BY TIME DESC")


            try:
                ranker_role = self.bot.get_guild(guild.id).get_role(int(ranker_role['ROLE_ID']))
                for idx, user in enumerate(users):
                    member = guild.get_member(int(user['MEMBER_ID']))
                    if idx == 0:
                        await member.add_roles(ranker_role)
                    else:
                        await member.remove_roles(ranker_role)
            except Exception:
                continue
                # print(f'{guild.id}, Ranker role not set or unknown error')
            

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
            if after.channel == before.channel:
                return
            
            # print(f'[LOG][{dt.datetime.utcnow() + dt.timedelta(hours=9)}] {member.name}#{member.discriminator} : {before} → {after}')

            if (after.channel != None and before.channel != None) or after.channel == None: # 통화방을 나갔거나 이동한 경우
                if self.voice_time[member.id]:
                    seconds = int(time.time() - self.voice_time[member.id]) # 통화시간 초단위
                    self.voice_time[member.id] = 0
                else:
                    return await before.channel.send(f'{member.mention} 님, 통화 시간을 저장하는 데에 알 수 없는 오류가 발생하였습니다. 해당 통화 시간을 저장하시려면 개발자에게 문의해주세요.')
                

                if self.config[member.guild.id]['notice']:
                    try:
                        await before.channel.send(embed=discord.Embed(description=f":no_entry: ``{member}`` 님이 ``{before.channel.name}`` 채널에서 퇴장하셨습니다.", color=color['red'])\
                            .set_footer(text=f"총 통화 시간 {dt.timedelta(seconds=seconds)}"))
                    except Exception:
                        pass
                
                if seconds > 5 and not member.bot: # 통화시간 저장 및 역할 업데이트
                    _time = await self.mysql.fetch_one_data(f"SELECT TIME FROM voice_time WHERE MEMBER_ID = {member.id} AND SERVER_ID = {member.guild.id}") # 유저 시간 가져오기
                    await self.mysql._execute(f"UPDATE voice_time SET TIME={seconds+_time['TIME']} WHERE MEMBER_ID = {member.id} AND SERVER_ID = {member.guild.id}")


                    # 역할 부여
                    seconds = await self.mysql.fetch_one_data(f"SELECT TIME FROM voice_time WHERE MEMBER_ID = {member.id} AND SERVER_ID = {member.guild.id}") # 해당 멤버의 통화 시간 가져오기
                    ranks = await self.mysql.fetch_all_data(f"SELECT ROLE_ID, TIME FROM voice_rank WHERE SERVER_ID = {member.guild.id} AND TIME <= {seconds['TIME']} ORDER BY TIME DESC")
                    if ranks != ():
                        if str(member.roles).find(ranks[0]['ROLE_ID']) == -1: # 역할을 찾지 못한 경우 랭크업
                            for rank in ranks[1:]: # 이전 역할들 다 제거
                                await member.remove_roles(self.bot.get_guild(member.guild.id).get_role(int(rank['ROLE_ID'])))
                            
                            upgrade_rank = self.bot.get_guild(member.guild.id).get_role(int(ranks[0]['ROLE_ID']))
                            await member.add_roles(upgrade_rank) # 새로운 역할 부여
                            
                            channel = await self.mysql.fetch_one_data(f"SELECT CHANNEL_ID FROM voice_rank_notice WHERE SERVER_ID = {member.guild.id}")
                            channel = int(channel['CHANNEL_ID'])
                            channel = self.bot.get_channel(channel)
                            await channel.send(':up:  {_user} 님이 ``{_time}`` 만큼의 통화 시간을 달성하셔서 <@&{_rank}> 역할을 획득하셨습니다!!'.format(
                                _user = member.mention,
                                _time = self.format_time(ranks[0]['TIME']),
                                _rank = ranks[0]['ROLE_ID']
                            ))

            
            if after.channel != None: # 채널 입장
                self.voice_time[member.id] = time.time()
                if self.config[member.guild.id]['notice']:
                    try:
                        await after.channel.send(embed=discord.Embed(description=f":bell: ``{member}`` 님이 ``{after.channel.name}`` 채널에 입장하셨습니다.", color=color['green']))
                    except Exception:
                        pass
                if not member.bot:
                    if await self.mysql.fetch_one_data(f"SELECT TIME FROM voice_time WHERE MEMBER_ID = {member.id} AND SERVER_ID = {member.guild.id}") is None:
                        await self.mysql._execute(f"INSERT INTO voice_time(SERVER_ID, MEMBER_ID) VALUES ({member.guild.id}, {member.id})")



    @app_commands.command(name="입퇴장", description="음성 채널의 입퇴장 알림 기능을 ON/OFF 합니다. (관리자 전용)")
    @app_commands.checks.has_permissions(administrator=True)
    async def notice(self, interaction:discord.Interaction):
        self.config[interaction.user.guild.id]['notice'] = not self.config[interaction.user.guild.id]['notice']
        await interaction.response.send_message("음성 채널의 입퇴장 알림을 {}습니다.".format('켰' if self.config[interaction.user.guild.id]['notice'] else '껐'), ephemeral=True)


    @app_commands.command(name="통화", description="통화 관련 명령어")
    @app_commands.choices(옵션=[
        app_commands.Choice(name="시간확인", value="시간확인"),
        app_commands.Choice(name="랭킹확인", value="랭킹확인"),
        app_commands.Choice(name="등급확인", value="등급확인")
    ])
    @app_commands.describe(멘션='멘션으로 입력')
    async def voice_command(self, interaction:discord.Interaction, 옵션:str, 멘션:str = ''):

        if 옵션 == '시간확인':

            search_id = interaction.user.id if 멘션 == '' else 멘션.replace('<@', '').replace('>', '')

            _time = await self.mysql.fetch_one_data(f"SELECT TIME FROM voice_time WHERE MEMBER_ID = {search_id} AND SERVER_ID = {interaction.user.guild.id}")
            if _time is None:
                await interaction.response.send_message('서버에서 통화한 기록이 없습니다.', ephemeral=True)
            else:
                await interaction.response.send_message('<@{mention}> 님이 서버에서 통화한 시간은 총 ``{time}`` 입니다.'.format(
                    mention = search_id,
                    time=self.format_time(_time['TIME'])), ephemeral=True)

        elif 옵션 == '랭킹확인':
            data = await self.mysql.fetch_all_data(f"SELECT MEMBER_ID, TIME FROM voice_time WHERE SERVER_ID = {interaction.user.guild.id} ORDER BY TIME DESC")
            embed = discord.Embed(title='[통화 시간 랭킹]', color=0x00FF1D)
            for i in range(len(data) if len(data) < 10 else 10):
                user = self.bot.get_user(int(data[i]['MEMBER_ID']))

                embed.add_field(name=f"{i+1}등 {user.display_name}", value=f"└총 통화 시간 ``{self.format_time(data[i]['TIME'])}``", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif 옵션 == '등급확인':
            ranks = await self.mysql.fetch_all_data(f"SELECT ROLE_ID, TIME FROM voice_rank WHERE SERVER_ID = {interaction.user.guild.id} AND TIME <= 2100000000 ORDER BY TIME DESC")
            if ranks != ():
                await interaction.response.send_message('\n\n'.join(["<@&{0}> = ``{1}``".format(rank['ROLE_ID'], self.format_time(rank['TIME'])) for rank in ranks]), ephemeral=True)
            else:
                await interaction.response.send_message('서버에 설정된 등급이 없습니다.', ephemeral=True)

                

    @app_commands.command(name='통화랭크', description='통화 랭크설정 관련 명령어 (관리자 전용)')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(역할='역할 멘션으로 입력', 시간='초 단위로 입력')
    @app_commands.choices(옵션=[
        app_commands.Choice(name="랭크추가", value='추가'),
        app_commands.Choice(name="랭크제거", value='제거'),
        app_commands.Choice(name="알림설정", value='알림'),
        app_commands.Choice(name="랭커설정", value='랭커')
    ])
    async def admin_voice_command(self, interaction:discord.Interaction, 옵션:str, 역할:str='', 시간:int = 0):

        역할 = 역할.replace('<@&', '').replace('>', '')

        if 옵션 == '추가': # 랭크추가
            await self.mysql._execute(f"INSERT INTO voice_rank(SERVER_ID, ROLE_ID, TIME) VALUES({interaction.user.guild.id}, {역할}, {시간})")
            await interaction.response.send_message('누적 통화 시간이 ``{0}`` 가 되면 {1} 역할을 획득하게 설정하였습니다. '.format(self.format_time(시간), '<@&' + 역할 + '>'), ephemeral=True)

        elif 옵션 == '제거': # 랭크제거
            await self.mysql._execute(f"DELETE FROM voice_rank WHERE ROLE_ID = {역할}")
            await interaction.response.send_message('역할 설정에서 {0} 을 제거하였습니다.'.format('<@&' + 역할 + '>'), ephemeral=True)
        
        elif 옵션 == '랭커':
            await self.mysql._execute(f'INSERT INTO voice_ranker (SERVER_ID, ROLE_ID) VALUES ({interaction.user.guild.id}, {역할}) ON DUPLICATE KEY UPDATE SERVER_ID={interaction.user.guild.id}, ROLE_ID={역할}')
            await interaction.response.send_message('통화 시간 랭킹이 1위인 경우 {0} 역할을 획득하게 설정하였습니다. (6시간마다 갱신)'.format('<@&' + 역할 + '>'), ephemeral=True)

        elif 옵션 == '알림': # 알림
            await self.mysql._execute(f"REPLACE INTO voice_rank_notice(SERVER_ID, CHANNEL_ID) VALUES({interaction.user.guild.id}, {interaction.channel_id})")
            await interaction.response.send_message('이 채널을 랭크 알림 채널로 설정하였습니다.', ephemeral=True)
        

    @app_commands.command(name="색상", description="통화랭커 역할의 색상을 설정합니다.")
    @app_commands.describe(색상='10진수 정수 컬러 값 입력')
    async def ranker_color(self, interaction:discord.Interaction, 색상:int):
        ranker_role = await self.mysql.fetch_one_data(f"SELECT ROLE_ID FROM voice_ranker WHERE SERVER_ID = {interaction.guild.id}")
        ranker_user = await self.mysql.fetch_one_data(f"SELECT MEMBER_ID, TIME FROM voice_time WHERE SERVER_ID = {interaction.guild.id} ORDER BY TIME DESC")
        if int(ranker_user['MEMBER_ID']) == interaction.user.id:
            ranker_role = discord.utils.get(interaction.guild.roles, id=int(ranker_role['ROLE_ID']))
            await ranker_role.edit(colour=discord.Colour(색상))
            await interaction.response.send_message(f'역할 색상이 변경되었습니다.\t{ranker_role.mention}', ephemeral=True)
        else:
            await interaction.response.send_message('통화 랭킹 1등만 색 설정이 가능합니다.', ephemeral=True)



        

    def format_time(self, second:int): # 초단위 -> 시간포맷 (n일 n시간 n분 n초)
        _time = str(dt.timedelta(seconds=second)).replace(' days, ', ':').replace(' day, ', ':').split(':') # 시간 포맷
        if len(_time) != 4:
            for i in range(4 - len(_time)):
                _time.insert(i, '0')
        return f'{_time[0]}일 {_time[1]}시간 {_time[2]}분 {_time[3]}초'

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))