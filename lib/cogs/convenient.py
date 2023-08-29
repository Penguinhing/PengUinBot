import discord, random
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View

class Convenient(commands.Cog):

    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.voice_region = ('brazil', 'hongkong', 'india', 'japan', 'rotterdam', 'russia', 'singapore', 'south-korea', 'southafrica', \
                                    'sydney', 'us-central', 'us-east', 'us-south', 'us-west') # 통화 지역

    @app_commands.command(name="팀짜기", description="접속 중인 통화방 인원들을 토대로 랜덤 팀을 구성합니다.")
    @app_commands.describe(구성팀="몇 개의 팀으로 구성할지 입력")
    async def random_team(self, interaction:discord.Interaction, 구성팀:int):
        if interaction.user.voice:
            channel = self.bot.get_channel(interaction.user.voice.channel.id)
            members = channel.members
            if len(members) < 구성팀 or 구성팀 <= 0:
                return await interaction.response.send_message("구성팀이 너무 많습니다.", ephemeral=True)
            
            random.shuffle(members)
            text = f'접속중인 통화방 인원들을 토대로 {구성팀}개의 팀을 랜덤으로 구성하였습니다.'
            teams = [[f'\n\n**=== {chr(65+i)}팀 ===**'] for i in range(구성팀)]
            set_team = 0
            for m in members:
                teams[set_team] += ["``" + m.display_name + "``"]
                set_team = 0 if 구성팀-1 < set_team+1 else set_team+1

            for t in teams:
                text += "\n".join(t)

            await interaction.response.send_message(text)
        else:
            await interaction.response.send_message("접속 중인 통화 채널이 없습니다.", ephemeral=True)


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


    @app_commands.command(name="청소", description="갯수만큼 채널의 메시지를 삭제합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def cleanup(self, interaction:discord.Interaction, 갯수:int):
        await interaction.response.defer()
        await interaction.channel.purge(limit=갯수+1)




async def setup(bot):
    await bot.add_cog(Convenient(bot))