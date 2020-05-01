"""This is a cog for a discord.py bot.
It will add some superuser commands to a bot.

Commands:
    git
      pull       pull latest changes from github
      reset      reset n commits

Only users which are specified as a superuser in the config.json
can run commands from this cog.
"""

import re
import subprocess
import json
from ast import literal_eval
from discord.ext import commands


class Superuser(commands.Cog, name='Superuser'):
    def __init__(self, client):
        self.client = client
        self.cog_re = re.compile(
            r'\s*python\/cogs\/(.+)\.py\s*\|\s*\d+\s*[+-]+'
        )

    async def cog_check(self, ctx):
        return self.client.user_is_superuser(ctx.author)

    # ----------------------------------------------
    # Command to pull the latest changes from github
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
            return await ctx.send(str(e))

        _cogs = [f'cogs.{i}' for i in self.cog_re.findall(output)]
        active_cogs = [i for i in _cogs if i in self.client.extensions]
        if active_cogs:
            for cog_name in active_cogs:
                await ctx.invoke(self.client.get_command('reload'), cog_name)

    # ----------------------------------------------
    # Command to reset the repo to a previous commit
    # ----------------------------------------------
    @git.command(
        name='reset',
    )
    async def reset(self, ctx, n: int):
        """Reset repo to HEAD~[n]"""
        if not n > 0:
            raise commands.BadArgument('Please specify n>0')
        await ctx.trigger_typing()
        try:
            output = subprocess.check_output(
                ['git', 'reset', '--hard', f'HEAD~{n}']).decode()
            await ctx.send('```git\n' + output + '\n```')
        except Exception as e:
            await ctx.send(str(e))

    # ----------------------------------------------
    # Command to change a setting in the config file
    # ----------------------------------------------
    @commands.command(
        name='setting',
    )
    async def setting(self, ctx, setting_name: str, setting_value):
        """Change a setting

        Be careful with this one, as it could overwrite the bot_key or similar settings"""
        with open("../config.json") as conffile:
            self.client.config = json.load(conffile)

        self.client.config[setting_name] = literal_eval(setting_value)

        with open("../config.json", 'w') as conffile:
            json.dump(self.client.config, conffile, indent=1)

        await ctx.send('`Success`')

def setup(client):
    client.add_cog(Superuser(client))
