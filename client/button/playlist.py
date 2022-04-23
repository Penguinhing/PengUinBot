import asyncio, discord
from client.module.MusicHelper import MusicHelper
from discord.ui import Button, View
from client.module.Setting import *


class Playlist(View):


	def __init__(self, ctx, user_id=None):
		super().__init__(timeout=None)
		self.ctx = ctx
		self.page = 1
		self.max_page = 0
		self.playlist = None
		self.user_id = user_id
		self.reload()

	async def on_timeout(self):
		pass
	
	def reload(self):
		self.playlist = MusicHelper(ctx=self.ctx).load_playlist(user_id=self.user_id)
		if len(self.playlist) <= 5:
			self.max_page = 0
		elif len(self.playlist) % 5 == 0:
			self.max_page = int(len(self.playlist) / 5)
		else:
			self.max_page = int(len(self.playlist) / 5) + 1

	@discord.ui.button(label="<<", style=discord.ButtonStyle.gray)
	async def perv_page(self, interaction, button):
		self.reload()
		if self.page - 1 < 1:
			return
		self.page -= 1
	
		await interaction.response.edit_message(embed=discord.Embed(title="{0}님의 재생 목록".format(self.ctx.author.name) if self.user_id != None else '재생 목록', description='\n'.join\
			([f"{(self.page * 5 - 5) + i + 1}. {name.split('---')[1]}" for i, name in enumerate(self.playlist[self.page * 5 - 5:(self.page+1) * 5 -5])]), color=color['sky'])\
				.set_footer(text=f"{self.page}/{self.max_page}").set_thumbnail(url='https://i.imgur.com/nMxWMtB.png'), view=self)
	
	@discord.ui.button(label=">>", style=discord.ButtonStyle.gray)
	async def next_page(self, interaction, button):
		self.reload()
		if self.page + 1 > self.max_page:
			return
		self.page += 1
		
		await interaction.response.edit_message(embed=discord.Embed(title="{0}님의 재생 목록".format(self.ctx.author.name) if self.user_id != None else '재생 목록', description='\n'.join\
			([f"{(self.page * 5 - 5) + i + 1}. {name.split('---')[1]}" for i, name in enumerate(self.playlist[5*self.page-5:5*self.page])]), color=color['sky'])\
				.set_footer(text=f"{self.page}/{self.max_page}").set_thumbnail(url='https://i.imgur.com/nMxWMtB.png'), view=self)

