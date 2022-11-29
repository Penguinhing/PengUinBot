import discord
from discord.ui import Button, View


class queue_btn(View):
    def __init__(self, ctx, msg, embed, playlist, obj):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.msg = msg
        self.playlist = playlist
        self.now_page = 1
        self.max_page = int(len(playlist) / 5) + 1 if len(playlist) % 5 != 0 else 0
        self.embed = embed
        self.obj = obj # 객체

    async def interaction_check(self, interaction) -> bool:
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
                return False
            return True
    
    @discord.ui.button(label='<< 이전 페이지', style=discord.ButtonStyle.grey)
    async def perv(self, interaction, button):
        if self.now_page-1 >= 1:
            self.now_page -= 1
            await self.set_page()
            await interaction.response.defer()
        else:
            await interaction.response.send_message('이전 페이지가 존재하지 않아요.', ephemeral=True)

    @discord.ui.button(label='새로고침', style=discord.ButtonStyle.grey)
    async def reset(self, interaction, button):
        self.playlist = [f"{i+1}. " + song[1] for i, song in enumerate(self.obj.playlist[self.ctx.guild.id])]
        self.now_page = 1
        await self.set_page()
        await interaction.response.send_message('재생 목록을 새로고침 하였습니다!', ephemeral=True)
    

    @discord.ui.button(label='다음 페이지 >>', style=discord.ButtonStyle.grey)
    async def next(self, interaction, button):
        if self.now_page+1 <= self.max_page:
            self.now_page += 1
            await self.set_page()
            await interaction.response.defer()
        else:
            await interaction.response.send_message('다음 페이지가 존재하지 않아요.', ephemeral=True)
    


    async def set_page(self): # 현재 페이지를 기준으로 5개의 리스트를 반환
        self.embed.set_footer(text=f'{self.now_page}/{self.max_page} 페이지')
        self.embed.description = '\n'.join(self.playlist[5 * (self.now_page-1):5 * self.now_page])
        await self.msg.edit(embed=self.embed)