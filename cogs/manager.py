import discord
from discord import app_commands
from discord.ext import commands


class ManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="청소", description="갯수만큼 채널의 메시지를 삭제합니다. (관리자 전용)")
    @app_commands.checks.has_permissions(administrator=True)
    async def cleanup(self, interaction:discord.Interaction, 갯수:int):
        await interaction.response.send_message(f"채널에서 {갯수}개의 메시지를 삭제했습니다.", ephemeral=True)
        await interaction.channel.purge(limit=갯수)
        

async def setup(bot):
    await bot.add_cog(ManagerCog(bot))