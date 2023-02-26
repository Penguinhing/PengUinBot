import discord, asyncio
from discord import app_commands
from discord.ext import commands


class ManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.streamings = dict()
    
    @app_commands.command(name="청소", description="갯수만큼 채널의 메시지를 삭제합니다. (관리자 전용)")
    @app_commands.checks.has_permissions(administrator=True)
    async def cleanup(self, interaction:discord.Interaction, 갯수:int):
        await interaction.response.defer()
        await interaction.channel.purge(limit=갯수+1)


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        
        
        self.stream_role = 1079332901130350643 # 방송 권한 역할 ID
        self.reconnect_channel = 1003253835357237319 # 재접속할때 이동시킬 채널 ID

        if str(member.roles).find(str(self.stream_role)) != -1: # 방송 권한이 있는 경우 return
            return

        # 방송을 켠 경우
        if after.self_stream:
            self.streamings[member.id] = True

            # 180초, 5초마다 체크
            for i in range(36):
                await asyncio.sleep(5)
                if not self.streamings[member.id]: # 중간에 방송이 종료된 경우 함수 종료
                    return self.streamings.pop(member.id)
            
            # 재접속
            original_channel = after.channel.id
            await member.move_to(self.bot.get_channel(self.reconnect_channel))
            await member.move_to(self.bot.get_channel(original_channel))
        
        elif self.streamings.get(member.id):
            self.streamings[member.id] = False




async def setup(bot):
    await bot.add_cog(ManagerCog(bot))