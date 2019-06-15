"""This is a cog for a discord.py bot.
It hides the help command and adds these commands:

    helpall     show all commands (including all hidden ones)

    The commands will output to the current channel or to a dm channel
    according to the pm_help kwarg of the bot.

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from discord.ext.commands import DefaultHelpCommand


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.get_command('help').hidden = True

    async def cog_check(self, ctx):
        return self.client.user_has_permission(ctx.author, 'helpall')

    def cog_unload(self):
        self.client.get_command('help').hidden = False

    @commands.command(
        name='helpall',
        brief='Show this message',
        hidden=True
    )
    @commands.guild_only()
    async def helpall(self, ctx):
        self.client.help_command = DefaultHelpCommand(show_hidden=True)
        await ctx.send_help()
        self.client.help_command = DefaultHelpCommand()


def setup(client):
    client.add_cog(Help(client))
