import discord
from discord.ui import Button, View


class Active(View):
	def __init__(self, ctx):
		super().__init__(timeout=15)
		self.ctx = ctx
	
	async def interaction_check(self, interaction) -> bool:
		if interaction.user != self.ctx.author:
			await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
			return False
		return True


	@discord.ui.button(emoji='1️⃣', style=discord.ButtonStyle.grey)
	async def number_1(self, interaction, button):
		await interaction.response.send_message('1')
	
	@discord.ui.button(emoji="2️⃣", style=discord.ButtonStyle.grey)
	async def number_2(self, interaction, button):
		await interaction.response.send_message('2')

	@discord.ui.button(emoji="3️⃣", style=discord.ButtonStyle.grey)
	async def number_3(self, interaction, button):
		await interaction.response.send_message('3')

	@discord.ui.button(emoji="4️⃣", style=discord.ButtonStyle.grey)
	async def number_4(self, interaction, button):
		await interaction.response.send_message('4')

	@discord.ui.button(emoji="5️⃣", style=discord.ButtonStyle.grey)
	async def number_5(self, interaction, button):
		await interaction.response.send_message('5')
