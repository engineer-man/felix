"""This is a cog for a discord.py bot.
It will add some superuser commands to a bot.

Commands:
    pull       pull latest changes from github

Only users which are specified as a superuser in the config.json
can run commands from this cog.
"""

import subprocess
from discord.ext import commands


class Superuser(commands.Cog, name='Superuser'):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return self.client.user_is_superuser(ctx.author)

    # ----------------------------------------------
    # Function to pull the latest changes from github
    # ----------------------------------------------
    @commands.group(
        invoke_without_command=True,
        name='git',
        hidden=True,
    )
    async def git(self, ctx):
        """Commands to run git commands on the local repo"""
        await ctx.send_help('git')

    @git.command(
        name='pull',
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

    # ----------------------------------------------
    # Function to reset the repo to a previous commit
    # ----------------------------------------------
    @git.command(
        name='reset',
    )
    async def reset(self, ctx, n):
        """Reset repo to HEAD~[n]"""
        if not n>0:
            raise commands.BadArgument('Please specify n>0')
        await ctx.trigger_typing()
        try:
            output = subprocess.check_output(
                ['git', 'reset', '--hard', f'HEAD~{n}']).decode()
            await ctx.send('```git\n' + output + '\n```')
        except Exception as e:
            await ctx.send(str(e))

def setup(client):
    client.add_cog(Superuser(client))
