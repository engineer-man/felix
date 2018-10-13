import discord
from discord.ext import commands
import random
from os import path
import json

questions = open('questions.txt').read().splitlines()

def is_cc_channel():
    """Used as a decorator for bot commands
    to make sure only staff can see/use it
    """
    async def predicate(ctx):
        return ctx.channel.id == 485581363383107604
    return commands.check(predicate)

class insults:
    def __init__(self, bot):
        self.bot = bot
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            self.permitted_roles = json.load(f)[__name__.split('.')[-1]]


    async def __local_check(self, ctx):
        # if await ctx.bot.is_owner(ctx.author):
        #     return True
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    @commands.command()
    @is_cc_channel()
    async def insult(self, ctx):
        await ctx.send(random.choice(questions))

def setup(bot):
    bot.add_cog(insults(bot))
