from random import randint
from datetime import timedelta

import asyncio, discord, math, time
from discord.ext import commands
from discord import app_commands

from lib.sql.data import Query
from lib.btns.paging import Page



class Exp(commands.Cog):

    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.query = Query()
        self.anti_spam = {}
        self.voice_times = {}
        
    @app_commands.command(name="경험치지급", description="유저에게 경험치를 지급합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def give_custom_exp(self, interaction:discord.Interaction, 멘션 : str, exp : int = 0):
        await self.update_member(str(interaction.guild.id), 멘션.replace('<@', '').replace('>', ''), exp)
        
        await interaction.response.send_message(f"관리자가 {멘션} 님에게 {exp:,} EXP 를 지급하였습니다.")

    @app_commands.command(name="정보", description="자기 자신 또는 다른 사람의 정보를 확인합니다.")
    async def check_info(self, interaction:discord.Interaction, 멘션:str = None):

        search_id = int(멘션.replace('<@', '').replace('>', '')) if 멘션 else interaction.user.id

        members = self.query.fetchAll("SELECT MEMBER_ID, EXP, VOICE_TIME FROM member_info WHERE SERVER_ID = {server_id} ORDER BY EXP DESC"
                                      .format(server_id=interaction.guild.id))
        for ranking, member in enumerate(members):
            if int(member['MEMBER_ID']) == search_id:
                    
                user = self.bot.get_user(search_id)

                now_exp = int(member['EXP'])

                now_level = self.exp_to_level(now_exp)
                next_level_exp = now_exp - self.level_to_exp(now_level)
                voice_time = self.format_time(int(member['VOICE_TIME']))
                

                embed = discord.Embed(color=3145631).set_thumbnail(url="https://i.imgur.com/Hd4sl1N.png")
                embed.set_author(name=f"{user.display_name} 님의 정보", icon_url=user.display_avatar)
                embed.add_field(name="현재 레벨", value=f"Lv.{now_level} ({now_exp:,} EXP) \n\u200b", inline=False)
                embed.add_field(name="다음 레벨까지 남은 경험치", value=f"{next_level_exp:,} / {(now_level+1) * 1000:,} EXP \n\u200b", inline=False)
                embed.add_field(name="총 통화 시간", value=f"{voice_time} \n\u200b", inline=False)
                embed.add_field(name="서버 랭킹", value=f"{ranking+1}위", inline=False)
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.send_message("서버에 등록된 정보가 없습니다.", ephemeral=True)


    
    @app_commands.command(name="서버랭킹", description="서버 멤버들의 경험치 랭킹을 확인합니다.")
    @app_commands.checks.cooldown(1, 30.0, key=None)
    async def check_ranking(self, interaction:discord.Interaction):

        members = self.query.fetchAll("SELECT MEMBER_ID, EXP, VOICE_TIME FROM member_info WHERE SERVER_ID = {server_id} ORDER BY EXP DESC"
                                      .format(server_id=interaction.guild.id))
        contents = []
        ranking = 1
        for member in members:


            user = self.bot.get_user(int(member['MEMBER_ID']))
            if user == None:
                continue


            contents += [{
                'name': "{ranking}위 {display_name} (Lv.{now_level})".format(
                ranking = ranking,
                display_name = user.display_name,
                now_level = self.exp_to_level(int(member['EXP']))
                ),
                'description':"- 통화 시간: {voice_time}\
                    \n- 획득한 경험치: {exp:,} EXP".format(
                voice_time = self.format_time(member['VOICE_TIME']),
                    exp = member['EXP']
                    )}]
            ranking += 1

        embed = discord.Embed(title="[서버 랭킹]", color=16711680).set_thumbnail(url="https://i.imgur.com/Hd4sl1N.png")

        await interaction.response.defer()
        message : discord.WebhookMessage = await interaction.followup.send(embed=embed)


        page = Page(message, embed, contents)
        await message.edit(view=page)
        await page.set_page()
        

    @commands.Cog.listener()
    async def on_voice_state_update(self, member : discord.Member, before : discord.VoiceState, after : discord.VoiceState):
            
            if member.bot:
                return

            key = member.guild.id + member.id
            if after.channel is None:
                if key in self.voice_times:
                    total_voice_time = int(time.time() - self.voice_times[key])
                    del self.voice_times[key]
                    if total_voice_time > 5:
                        await self.update_member(server_id=member.guild.id, member_id=member.id, exp=total_voice_time, voice_time=total_voice_time)
                        print(f"[SAVE] {member.name} -> {total_voice_time} second")

            elif before.channel != after.channel:
                if not (key in self.voice_times): # 통화방을 이동하지 않고 그냥 처음 입장한 경우
                    self.voice_times[key] = time.time()




    @commands.Cog.listener()
    async def on_message(self, message : discord.Message):
        if message.author.bot: 
            return
        
        if not message.author.id in self.anti_spam:
            self.anti_spam[message.author.id] = 0


        if self.anti_spam[message.author.id] == 0:
            await self.update_member(message.guild.id, message.author.id, exp=randint(100, 300))

        
        self.anti_spam[message.author.id] += 1
        await asyncio.sleep(5)
        self.anti_spam[message.author.id] -= 1






    async def update_member(self, server_id : str, member_id : str, exp:int = 0, voice_time : int = 0) -> dict:

        self.query.execute("INSERT INTO member_info(SERVER_ID, MEMBER_ID, EXP, VOICE_TIME) VALUES ('{server_id}', '{member_id}', {exp}, {voice_time})\
                                  ON DUPLICATE KEY UPDATE EXP=EXP+{exp}, VOICE_TIME=VOICE_TIME+{voice_time}".format(
                                    server_id = server_id,
                                    member_id = member_id,
                                    exp = exp,
                                    voice_time = voice_time
                                  ))
        
        
        member_info = self.query.fetchOne("SELECT EXP FROM member_info WHERE SERVER_ID = '{server_id}' AND MEMBER_ID = '{member_id}'".format(
            server_id = server_id,
            member_id = member_id))
        
        prev_level = self.exp_to_level(member_info['EXP'] - exp)
        now_level = self.exp_to_level(member_info['EXP'])


        if prev_level != now_level:


            # 랭크 부분
            rankup = False
            ranks = self.query.fetchAll("SELECT * FROM ranks WHERE SERVER_ID = '{server_id}' AND LEVEL <= {now_level} ORDER BY LEVEL DESC"
                                .format(server_id = server_id, now_level = now_level))
            guild = self.bot.get_guild(int(server_id))
            member = guild.get_member(int(member_id))
            if ranks:
                rank_up_role_id = int(ranks[0]['ROLE_ID'].replace('<@&', '').replace('>', ''))
                if member.get_role(rank_up_role_id) is None: # 랭크업 체크
                    for rank in ranks[1:]: # 이전 랭크의 역할들 모두 제거
                        role = member.get_role(int(rank['ROLE_ID'].replace('<@&', '').replace('>', '')))
                        if role:
                            await member.remove_roles(role)
                    
                    # 새로운 역할 지급
                    await member.add_roles(guild.get_role(rank_up_role_id))
                    rankup = rank_up_role_id




            server = self.query.fetchOne("SELECT LOG_CHANNEL FROM server_info WHERE SERVER_ID = {server_id}".format(server_id=server_id))
            if server: # 서버의 로그 채널이 있는 경우
                log_channel = self.bot.get_channel(int(server['LOG_CHANNEL']))

                # 레벨업 embed 메시지 생성
                embed_levelup = discord.Embed(title = "LEVEL UP !!", description="{mention} 님이 레벨업 하셨습니다!"
                    .format(mention = member.mention), color=3145538)
                embed_levelup.set_author(name="{prev_level} -> {now_level}".format(prev_level=prev_level, now_level=now_level)
                                 , icon_url=self.bot.user.avatar).set_footer(text="현재 레벨: {now_level}".format(now_level=now_level))
                embed_levelup.set_image(url="https://i.imgur.com/Bnoa9jD.png")
                await log_channel.send(embed=embed_levelup)

                if rankup:
                    embed_rankup = discord.Embed(title="RANK UP !!", description="{mention} 님이 <@&{role_id}> 등급으로 승급하셨습니다!"
                        .format(mention=member.mention, role_id = rankup), color=16734463)
                    embed_rankup.set_thumbnail(url="https://i.imgur.com/jKrMCkW.png")
                    await log_channel.send(embed=embed_rankup)
        return member_info
    



    def exp_to_level(self, exp : int):
        return int(math.sqrt(2 * exp / 1000 + 0.25) - 0.5)

    def level_to_exp(self, level : int):
        return int(level * (level + 1) * 1000 / 2)


    def format_time(self, seconds):
        time_delta = timedelta(seconds=seconds)
        days = time_delta.days
        hours, remainder = divmod(time_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{days}일 {hours}시간 {minutes}분 {seconds}초"
        return formatted_time




async def setup(bot):
    await bot.add_cog(Exp(bot))
