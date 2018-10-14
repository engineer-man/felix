import discord
from discord.ext import commands
import random
from os import path
import json

questions = open('questions.txt').read().splitlines()

def is_cc_channel():
    """Used as a decorator for bot commands to make them
    only useable in the em/command center channel
    """
    async def predicate(ctx):
        return ctx.channel.id == 485581363383107604
    return commands.check(predicate)

class Insults:
    def __init__(self, client):
        self.client = client
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

    @commands.command(name='insult',
                      brief='Make felix post a random insult',
                      description='Make felix post a random insult',
                      hidden=True,)
    @is_cc_channel()
    async def insult(self, ctx):
        await ctx.send(random.choice(questions))

def setup(client):
    client.add_cog(Insults(client))
