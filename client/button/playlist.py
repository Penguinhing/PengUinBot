import asyncio, discord
from client.module.MusicHelper import MusicHelper
from discord.ui import Button, View
from client.module.Setting import *


class Playlist(View):


	def __init__(self, ctx):
		super().__init__(timeout=None)
		self.ctx = ctx
		self.page = 1

	async def on_timeout(self):
		pass
	


	@discord.ui.button(label="<<", style=discord.ButtonStyle.gray)
	async def perv_page(self, button, interaction):

		if self.page - 1 < 1:
			return
		self.page -= 1
		playlist = MusicHelper(ctx=self.ctx).load_playlist()
		max_page = int(len(playlist) / 5 + 1) if len(playlist) != 1 and len(playlist) % 5 >= 1 else 0
		

		await interaction.response.edit_message(embed=discord.Embed(title="재생 목록", description='\n'.join\
			([f"{(self.page * 5 - 5) + i + 1}. {name.split('---')[1]}" for i, name in enumerate(playlist[self.page * 5 - 5:(self.page+1) * 5 -5])]), color=color['sky'])\
				.set_footer(text=f"{self.page}/{max_page}").set_thumbnail(url='https://i.imgur.com/nMxWMtB.png'), view=self)
	
	@discord.ui.button(label=">>", style=discord.ButtonStyle.gray)
	async def next_page(self, button, interaction):

		playlist = MusicHelper(ctx=self.ctx).load_playlist()
		max_page = int(len(playlist) / 5 + 1) if len(playlist) != 1 and len(playlist) % 5 >= 1 else 0
		if self.page + 1 > max_page:
			return
		self.page += 1
		
		await interaction.response.edit_message(embed=discord.Embed(title="재생 목록", description='\n'.join\
			([f"{(self.page * 5 - 5) + i + 1}. {name.split('---')[1]}" for i, name in enumerate(playlist[5*self.page-5:5*self.page])]), color=color['sky'])\
				.set_footer(text=f"{self.page}/{max_page}").set_thumbnail(url='https://i.imgur.com/nMxWMtB.png'), view=self)

