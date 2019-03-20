"""This is a cog for a discord.py bot.
it prints out the links to the GitHub repositories

Commands:
    source

Load the cog by calling client.load_extension with the name of this python file
as an argument (without .py)
    example:    bot.load_extension('example')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('folder.example')

"""

from discord.ext import commands
from os import path
import json

class Source(commands.Cog, name='Source'):
    def __init__(self, client):
        self.client = client
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            self.permitted_roles = json.load(f)[__name__.split('.')[-1]]

    async def cog_check(self, ctx):
        #return True
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    @commands.command(
        name='source',
        brief='Links to source code',
        description='Show all links to EMKC github repos',
        hidden=False,
    )
    async def source(self, ctx):
        await ctx.send('Youtube : <https://github.com/engineer-man/youtube-code>' +
        '\nEMKC: <https://github.com/engineer-man/emkc>' +
        '\nFelix: <https://github.com/engineer-man/felix>' +
        '\nPiston a.k.a. Felix run: <https://github.com/engineer-man/piston>')

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Source(client))
