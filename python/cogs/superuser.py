"""This is a cog for a discord.py bot.
It will add some superuser commands to a bot.

Commands:
    pull       pull latest changes from github

Only users which are specified as a superuser in the config.json
can run commands from this cog.
"""

from discord.ext import commands
import subprocess
import json


class Superuser(commands.Cog, name='Superuser'):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        superusers = self.client.config['superusers']
        return ctx.author.id in superusers

    # ----------------------------------------------
    # Function to pull the latest changes from github
    # ----------------------------------------------
    @commands.command(
        name='pull',
        hidden=True,
    )
    async def pull(self, ctx):
        """Pull the latest changes from github"""
        await ctx.trigger_typing()
        if not self.client.is_superuser(ctx.author):
            raise commands.CheckFailure(f'{ctx.author} is not a superuser')
        try:
            output = subprocess.check_output(
                ['git', 'pull']).decode()
            await ctx.send('```git\n' + output + '\n```')
        except Exception as e:
            await ctx.send(str(e))

    # Temp Command until DB is ported.
    @commands.command(
        name='id_map',
        hidden=True,
    )
    async def id_map(self, ctx):
        if not self.client.is_superuser(ctx.author):
            raise commands.CheckFailure(f'{ctx.author} is not a superuser')
        mapping = dict()
        for member in self.client.main_guild.members:
            mapping[str(member)] = member.id
        with open('id_mapping.json', 'w') as f:
            json.dump(mapping, f, indent=1)
        await ctx.send(f'Created mapping for {len(mapping)} users')

def setup(client):
    client.add_cog(Superuser(client))
