import discord
from discord.ui import Button, View
from view.setting import *


class Active(View):
    def __init__(self, parent, ctx):
        super().__init__(timeout=None)
        self.parent = parent
        self.ctx = ctx

        self.current_play = self.parent.playlist[self.ctx.guild.id][0][1] # 재생 중인 곡
        

    async def interaction_check(self, interaction) -> bool:
        if interaction.user != self.ctx.author or self.parent.playlist[self.ctx.guild.id][0][1] != self.current_play:
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return False
        return True
    

    @discord.ui.button(label='⏯️ 일시정지', style=discord.ButtonStyle.grey)
    async def pause(self, interaction, button):
        if self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
        elif self.ctx.voice_client.is_paused():
            self.ctx.voice_client.resume()

        await interaction.response.defer()

    @discord.ui.button(label='⏭️ 다음 곡', style=discord.ButtonStyle.grey)
    async def next(self, interaction, button):
        await self.parent.skip(self.ctx)


    @discord.ui.button(label='🔌 종료', style=discord.ButtonStyle.danger)
    async def next(self, interaction, button):
        await self.parent.leave(self.ctx)
