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
        return self.client.user_is_superuser(ctx.author)

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
        try:
            output = subprocess.check_output(
                ['git', 'pull']).decode()
            await ctx.send('```git\n' + output + '\n```')
        except Exception as e:
            await ctx.send(str(e))


def setup(client):
    client.add_cog(Superuser(client))
