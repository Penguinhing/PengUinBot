
import discord, datetime as dt
from view.setting import *
from discord.ext import commands
from discord import app_commands
from random import randint


class LevelCog(commands.Cog, name="LV"):

    def __init__(self, bot):
        self.bot = bot
        self.mysql = self.bot.get_cog('mysql')

    
    def get_UUID(self, server_id:int, member_id:int):
        return hex(int(server_id+member_id))


    def format_time(self, second:int): # 초단위 -> 시간포맷 (n일 n시간 n분 n초)
        _time = list(map(int, str(dt.timedelta(seconds=second)).replace(' days, ', ':').replace(' day, ', ':').split(':'))) # 시간 포맷
        if len(_time) != 4:
            for i in range(4 - len(_time)):
                _time.insert(i, 0)
        _time[1] += _time[0]*24    
        return f'{_time[1]}시간 {_time[2]}분 {_time[3]}초'



    async def give_exp(self, UUID:str, EXP:int, member:discord.Member):
        await self.mysql._execute(f"INSERT INTO user_info (SERVER_ID, MEMBER_ID, UUID, EXP, TOTAL_EXP) VALUES ('{member.guild.id}', '{member.id}', '{UUID}', {EXP}, {EXP}) ON DUPLICATE KEY UPDATE EXP=EXP+{EXP}, TOTAL_EXP=TOTAL_EXP+EXP;") # 경험치 지급

        user_info = await self.mysql.fetch_one_data(f"SELECT CURRENT_LEVEL, EXP FROM user_info WHERE UUID='{UUID}'")


        # 레벨업
        while user_info['EXP'] >= (user_info['CURRENT_LEVEL']+1) * 1000:
            user_info['CURRENT_LEVEL'] += 1
            user_info['EXP'] -= user_info['CURRENT_LEVEL'] * 1000
            await self.mysql._execute(f"UPDATE user_info SET CURRENT_LEVEL = {user_info['CURRENT_LEVEL']}, EXP = {user_info['EXP']} WHERE UUID='{UUID}';") # 레벨 업데이트
            notice = await self.mysql.fetch_one_data(f"SELECT CHANNEL_ID FROM level_up WHERE SERVER_ID='{member.guild.id}'")

            # 역할 업데이트
            get_role = None 
            roles = await self.mysql.fetch_all_data(f"SELECT ROLE_ID, CURRENT_LEVEL FROM level_role WHERE SERVER_ID = '{member.guild.id}'")
            if roles:
                for role in roles:
                    if role['CURRENT_LEVEL'] == user_info['CURRENT_LEVEL']:
                        for _role in roles: # 기존 역할들 모두 삭제
                            await member.remove_roles(self.bot.get_guild(member.guild.id).get_role(int(_role['ROLE_ID'].replace('<@&', '').replace('>', ''))))

                        await member.add_roles(self.bot.get_guild(member.guild.id).get_role(int(role['ROLE_ID'].replace('<@&', '').replace('>', '')))) # 새로운 역할 부여
                        get_role = role['ROLE_ID']
            
            # 알림
            if notice:
                notice = self.bot.get_channel(int(notice['CHANNEL_ID']))
                await notice.send(':up:  {_user} 님께서 레벨업 하셨습니다!\t``Lv.{_level}``'.format(_user = member.mention, _level=user_info['CURRENT_LEVEL']))

                if get_role:
                    await notice.send(':white_check_mark:  {_user} 님께서 {_role} 역할을 획득하셨습니다!'.format(_user = member.mention, _role=get_role))
               


    @app_commands.command(name="레벨", description="레벨 관련 명령어")
    @app_commands.choices(옵션=[
        app_commands.Choice(name="알림설정", value="알림설정"),
        app_commands.Choice(name="역할추가", value="역할추가"),
        app_commands.Choice(name="역할제거", value="역할제거"),
        app_commands.Choice(name="새로고침", value="새로고침"),
    ])
    @app_commands.describe(옵션='옵션을 선택해주세요.')
    @app_commands.checks.has_permissions(administrator=True)
    async def level_command(self, interaction:discord.Interaction, 옵션:str, 역할:str = None, 레벨:int = 256):
        if 옵션 == '알림설정':
            await self.mysql._execute(f"REPLACE INTO level_up(SERVER_ID, CHANNEL_ID) VALUES({interaction.user.guild.id}, {interaction.channel_id})")
            await interaction.response.send_message('이 채널을 레벨업 알림 채널로 설정하였습니다.', ephemeral=True)
        elif 옵션 == '역할추가':
            await self.mysql._execute(f"REPLACE INTO level_role(SERVER_ID, ROLE_ID, CURRENT_LEVEL) VALUES('{interaction.user.guild.id}', '{역할}', {레벨});")
            await interaction.response.send_message(f'Lv.{레벨} 을 달성하면 {역할} 역할을 얻게 설정하였습니다.', ephemeral=True)
        elif 옵션 == '역할제거':
            await self.mysql._execute(f"DELETE FROM level_role WHERE ROLE_ID = '{역할}'")
            await interaction.response.send_message(f'역할 목록에서 {역할} 역할을 제거하였습니다.', ephemeral=True)
        elif 옵션 == '새로고침':
            pass


    @app_commands.command(name="내정보", description="자기 자신의 레벨 정보를 확인합니다.")
    async def my_info(self, interaction:discord.Interaction):
        UUID = self.get_UUID(interaction.guild.id, interaction.user.id)

        user_infos = await self.mysql.fetch_all_data(f"SELECT UUID, VOICE_TIME, CURRENT_LEVEL, EXP, TOTAL_EXP FROM user_info WHERE SERVER_ID = {interaction.guild.id} ORDER BY TOTAL_EXP DESC;")
        
        for ranking, user_info in enumerate(user_infos):
            if user_info['UUID'] == UUID:
                now_exp = user_info['EXP']
                total_exp = user_info['TOTAL_EXP']
                next_exp = (user_info['CURRENT_LEVEL']+1) * 1000
                now_level = user_info['CURRENT_LEVEL']
                voice_time = self.format_time(user_info['VOICE_TIME'])
                embed=discord.Embed(color=color['green'])
                embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
                embed.add_field(name="현재 레벨", value=f"Lv.{now_level} ({total_exp:,} EXP) \n\u200b", inline=False)
                embed.add_field(name="다음 레벨까지 남은 경험치", value=f"{now_exp:,} / {next_exp:,} EXP \n\u200b", inline=False)
                embed.add_field(name="총 통화 시간", value=f"{voice_time} \n\u200b", inline=False)
                embed.add_field(name="서버 랭킹", value=f"{ranking+1}위", inline=False)
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        

        return await interaction.response.send_message('서버에 등록된 정보가 없습니다.', ephemeral=True)


    @app_commands.command(name="서버랭킹", description="각 멤버별 레벨 순위를 확인합니다.")
    async def server_ranking(self, interaction:discord.Interaction):
        user_infos = await self.mysql.fetch_all_data(f"SELECT MEMBER_ID, VOICE_TIME, CURRENT_LEVEL, EXP, TOTAL_EXP FROM user_info WHERE SERVER_ID = {interaction.guild.id} ORDER BY TOTAL_EXP DESC;")
        embed = discord.Embed(title='SERVER RANKING', color=color['purple'])

        for ranking, user_info in enumerate(user_infos):
            if ranking >= 10: break
            user = self.bot.get_user(int(user_info['MEMBER_ID']))
            now_level = f"(Lv.{user_info['CURRENT_LEVEL']})"
            voice_time = f"- 통화시간: {self.format_time(user_info['VOICE_TIME'])}\n"
            total_exp = f"- 획득한 경험치: {user_info['TOTAL_EXP']:,} EXP\n"
            embed.add_field(name=f"{ranking+1}위 {user.display_name} {now_level}", value=voice_time + total_exp + '\n\u200b', inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if not message.author.bot:
                await self.give_exp(UUID=self.get_UUID(server_id=message.author.guild.id, member_id=message.author.id), EXP=randint(100, 500), member=message.author)
        except AttributeError:
            pass
        

async def setup(bot):
    await bot.add_cog(LevelCog(bot))