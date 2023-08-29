import discord
from discord.ext import commands
from discord import app_commands
class CommandErrorHandler(commands.Cog):

    def __init__(self, bot : commands.Bot):
        bot.tree.on_error = self.global_app_command_error
        self.bot = bot


    @commands.Cog.listener()
    async def on_command_error(self, ctx : commands.Context, error):
        print(error)
        if isinstance(error, commands.MissingPermissions):
            return await ctx.send("작업을 수행하기 위한 권한이 없습니다.")

        
    
    async def global_app_command_error(self, interaction : discord.Interaction, error : app_commands.AppCommandError):
        print(error)
        if isinstance(error, app_commands.CommandInvokeError):
            return await interaction.response.send_message("입력 값이 올바른지 확인해주세요.", ephemeral=True)
        
        if isinstance(error, app_commands.MissingPermissions):
            return await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
        
        if isinstance(error, app_commands.CommandOnCooldown):
            return await interaction.response.send_message(f"{int(error.retry_after)}초 후에 사용 가능합니다.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))