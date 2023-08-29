import discord
from discord.ext import commands
from discord import app_commands
from lib.sql.data import Query


class Config(commands.Cog):

    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.query = Query()

    @app_commands.command(name="로그", description="봇의 로그 채널을 설정합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_log_channel(self, interaction : discord.Interaction):
        self.query.execute("INSERT INTO server_info(SERVER_ID, LOG_CHANNEL) VALUES('{server_id}', '{log_channel_id}') ON DUPLICATE KEY UPDATE LOG_CHANNEL = {log_channel_id};"
        .format(
            server_id= interaction.guild.id,
            log_channel_id = interaction.channel.id
        ))
        
        await interaction.response.send_message("현재 채널을 봇의 로그 채널로 설정하였습니다.", ephemeral=True)



    @app_commands.command(name="역할", description="레벨에 따라 지급할 역할을 추가/삭제 합니다.")
    @app_commands.choices(옵션=[
        app_commands.Choice(name="추가", value="추가"),
        app_commands.Choice(name="제거", value="제거"),
        app_commands.Choice(name="정보", value="정보"),
    ])
    @app_commands.describe(옵션='옵션을 선택해주세요.')
    @app_commands.checks.has_permissions(administrator=True)
    async def set_rank(self, interaction : discord.Interaction, 옵션 : str, 역할 : str = None, 레벨 : int = None):

        if 옵션 == '추가':
            if 역할 == None or 레벨 == None:
                return await interaction.response.send_message("역할과 레벨 정보를 올바르게 입력해주세요.", ephemeral=True)

            self.query.execute(
                "INSERT INTO ranks(SERVER_ID, LEVEL, ROLE_ID) VALUES('{server_id}', {level}, '{role_id}')".format(
                server_id = interaction.guild.id,
                level = 레벨,
                role_id = 역할
                )
            )
            await interaction.response.send_message(f"``Lv.{레벨}`` 에 도달하면 {역할} 역할을 얻도록 설정하였습니다.", ephemeral=True)


        elif 옵션 == '제거':

            if 역할 == None:
                return await interaction.response.send_message("역할 정보를 올바르게 입력해주세요.", ephemeral=True)

            self.query.execute(
                "DELETE FROM ranks WHERE ROLE_ID = '{role_id}'".format(
                role_id = 역할
                )
            )
            await interaction.response.send_message(f"역할 목록에서 {역할} 역할을 제거하였습니다.", ephemeral=True)


        else:
            roles = self.query.fetchAll(
                "SELECT * FROM ranks WHERE SERVER_ID = '{server_id}' ORDER BY LEVEL DESC"
                .format(server_id = interaction.guild.id)
            )
            if roles:
                text = "\n\n".join(["``Lv.{level}``    =    {role_id}".format(
                        level = role['LEVEL'],
                        role_id = role['ROLE_ID']
                    ) for role in roles])
                await interaction.response.send_message(text, ephemeral=True)
            else:
                await interaction.response.send_message("설정된 역할 정보가 없습니다.", ephemeral=True)



async def setup(bot):
    await bot.add_cog(Config(bot))