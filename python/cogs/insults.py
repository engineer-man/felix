import discord
from discord.ext import commands
import random

questions = open('questions.txt').read().splitlines()

class insults:
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def insult(self, ctx):
		if 498576446147788824 not in [y.id for y in ctx.message.author.roles]:
			await ctx.send("We are sorry but you can't use that command")
		else:
			if (ctx.message.channel.id != 483979023144189966):
				await ctx.send("You can't use that here.\nsilly duck")
			else:
				global question
				question = random.choice(questions)
				print(question)
				await ctx.send(question)

def setup(bot):
	bot.add_cog(insults(bot))
