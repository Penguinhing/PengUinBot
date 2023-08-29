from typing import Any, Coroutine
import discord
from discord.ui import Button, View


class Page(View):
    def __init__(self, message : discord.Message, 
                       embed : discord.Embed, 
                       contents : list,
                       ):
        super().__init__(timeout=60)
        self.message= message
        self.embed = embed
        

        self.page_size = 5
        self.max_page = max(1, (len(contents) // self.page_size) + (1 if len(contents) % self.page_size > 0 else 0))
        self.now_page = 1
        self.contents = contents


        for i in range(self.page_size):
            self.embed.add_field(name='', value='')

    # async def interaction_check(self, interaction : discord.Interaction) -> bool:
    #         if interaction.user != self.ctx.author:
    #             await interaction.response.send_message("조작 권한이 없습니다.", ephemeral=True)
    #             return False
    #         return True
    

    async def on_timeout(self):
        await self.message.delete()

    @discord.ui.button(label='<<', style=discord.ButtonStyle.grey)
    async def perv(self, interaction : discord.Interaction, button):
        self.now_page = max(1, self.now_page-5)
        await self.set_page()
        await interaction.response.defer()

    @discord.ui.button(label='<', style=discord.ButtonStyle.grey)
    async def perv_double(self, interaction : discord.Interaction, button):
        self.now_page = max(1, self.now_page-1)
        await self.set_page()
        await interaction.response.defer()

    @discord.ui.button(label='>', style=discord.ButtonStyle.grey)
    async def next(self, interaction : discord.Interaction, button):
        self.now_page = min(self.now_page+1, self.max_page)
        await self.set_page()
        await interaction.response.defer()

    @discord.ui.button(label='>>', style=discord.ButtonStyle.grey)
    async def next_double(self, interaction : discord.Interaction, button):
        self.now_page = min(self.now_page+5, self.max_page)
        await self.set_page()
        await interaction.response.defer()


    async def set_page(self):
        
        start = self.page_size * self.now_page - self.page_size
        end = start+self.page_size

        # 임시코드
        if self.now_page == self.max_page:
            for idx in range(5):
                self.embed.set_field_at(idx, name='', value='', inline=False)
        

        for idx, content in enumerate(self.contents[start:end]):
            self.embed.set_field_at(idx, name=content['name'], value=content['description'], inline=False)

        self.embed.set_footer(text=f'{self.now_page} / {self.max_page} 페이지')

        await self.message.edit(embed=self.embed)
