import discord, datetime
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Select, View


class ManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mysql = self.bot.get_cog('mysql') # mysql
        self.speaker.start()

        self.voice_region = ('brazil', 'hongkong', 'india', 'japan', 'rotterdam', 'russia', 'singapore', 'south-korea', 'southafrica', \
                             'sydney', 'us-central', 'us-east', 'us-south', 'us-west') # 통화 지역
        

    @app_commands.command(name="청소", description="갯수만큼 채널의 메시지를 삭제합니다. (관리자 전용)")
    @app_commands.checks.has_permissions(administrator=True)
    async def cleanup(self, interaction:discord.Interaction, 갯수:int):
        await interaction.response.defer()
        await interaction.channel.purge(limit=갯수+1)


    @app_commands.command(name="새로고침", description="현재 통화 채널의 서버를 새로운 서버로 변경합니다.")
    @app_commands.checks.cooldown(1, 10.0)
    async def refresh(self, interaction:discord.Interaction):
        if interaction.user.voice:

            # 선택 바
            select = Select(
                placeholder="변경할 지역을 골라주세요.",
                options=[ discord.SelectOption(label=v) for v in self.voice_region ])

            async def my_callback(interaction): # 선택바를 선택했을 경우
                await interaction.user.voice.channel.edit(rtc_region=select.values[0])
                await interaction.response.send_message(f"<@{interaction.user.id}> 님이 ``{interaction.user.voice.channel}`` 채널의 통화 지역을 ``{select.values[0]}`` (으)로 변경했습니다.")

            select.callback = my_callback # 선택바 출력
            await interaction.response.send_message(view=View(timeout=60).add_item(select), ephemeral=True)


            
        else:
            await interaction.response.send_message("접속 중인 통화 채널이 없습니다.", ephemeral=True)


    @refresh.error
    async def on_test_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)


    # 오후 9시, 오후 12시, 새벽 3시, 오후 4시
    @tasks.loop(time=[datetime.time(hour=15), datetime.time(hour=12), datetime.time(hour=18), datetime.time(hour=7)])
    async def speaker(self):
        for guild in self.bot.guilds: # 서버들 순회
            online_count = 0
            voice_count = 0
            notice = await self.mysql.fetch_one_data(f"SELECT CHANNEL_ID FROM level_up WHERE SERVER_ID='{guild.id}'")
            for member in guild.members:
                if member.status != discord.Status.offline:
                    online_count += 1
                if member.voice:
                    voice_count += 1

            icon = ':fire:' if voice_count >= 5 else ':green_circle:'
            notice = self.bot.get_channel(int(notice['CHANNEL_ID']))
            await notice.send(f'{icon} **현재 저희 서버는** ``{online_count}명``**이 온라인 상태이고** ``{voice_count}명``**이 통화 중입니다.**')
            if voice_count >= 10:
                await notice.send(":fire: :fire: :fire: **서버가 불타오르고 있습니다!!** :fire: :fire: :fire:")

                

async def setup(bot):
    await bot.add_cog(ManagerCog(bot))