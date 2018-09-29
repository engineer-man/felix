"""This is a cog for a discord.py bot.
It adds 2 commands

    help        show all non hidden commands + the commands from node_help.txt
    helpall     show all commands + the commands from node_help.txt

    The commands will output to the current channel or to a dm channel
    according to the pm_help kwarg of the bot.

The default help command has to be renamed to 'defaulthelp'
and should be hidden by constructing the bot with the
"help_attrs={'name': 'defaulthelp', 'hidden': True}" kwarg.

Load the cog by calling client.load_extension with the name of this python file
as an argument (without .py)
    example:    bot.load_extension('filename')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('my_extensions.filename')

Only people belonging to a group that is specified in the .allowed file
can use the commands.
"""

from discord.ext import commands
from discord.ext.commands.bot import _default_help_command
from discord.ext.commands.formatter import *


class myHelpFormatter(HelpFormatter):
    # Special Help Formatter that will include hidden commands
    def __init__(self, showHidden=False):
        super().__init__()
        self.show_hidden = showHidden

    async def format(self):
        """Handles the actual behaviour involved with formatting.

        To change the behaviour, this method should be overridden.

        Returns
        --------
        list
            A paginated output of the help command.
        """
        self._paginator = Paginator()

        # we need a padding of ~80 or so

        description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)

        if description:
            # <description> portion
            self._paginator.add_line(description, empty=True)

        if isinstance(self.command, Command):
            # <signature portion>
            signature = self.get_command_signature()
            self._paginator.add_line(signature, empty=True)

            # <long doc> section
            if self.command.help:
                self._paginator.add_line(self.command.help, empty=True)

            # end it here if it's just a regular command
            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            cog = tup[1].cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return cog + ':' if cog is not None else '\u200bNo Category:'

        filtered = await self.filter_command_list()
        if self.is_bot():
            data = sorted(filtered, key=category)
            for category, commands in itertools.groupby(data, key=category):
                # there simply is no prettier way of doing this.
                commands = sorted(commands)
                if len(commands) > 0:
                    self._paginator.add_line(category)

                self._add_subcommands_to_page(max_width, commands)
        else:
            filtered = sorted(filtered)
            if filtered:
                self._paginator.add_line('Commands:')
                self._add_subcommands_to_page(max_width, filtered)

        self._paginator.add_line('Node:')
        try:
            with open('node_help.txt') as f:
                node_help = f.read().strip()
                for line in node_help.split('\n'):
                    c, d = line.split(':')
                    num_spaces = max_width - len(c) + 1
                    self._paginator.add_line('  ' + c + ' '*num_spaces + d)
        except FileNotFoundError as e:
            print('node_help.txt not found', e)
        return self._paginator.pages


class Help():
    def __init__(self, client):
        self.client = client
        # Load id's of roles that are allowed to use commands from this cog
        with open(__file__.replace('.py', '.allowed')) as f:
            self.command_enabled_roles = [
                int(id) for id in f.read().strip().split('\n')
            ]


    async def __local_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False

        return any(role in self.command_enabled_roles for role in user_roles)

    # ----------------------------------------------
    # Custom help command
    # ----------------------------------------------
    @commands.command(
        name='help',
        brief='Show this message',
    )
    @commands.guild_only()
    async def newhelp(self, ctx):
        self.client.formatter = myHelpFormatter(False)
        await self.client.get_command('defaulthelp').invoke(ctx)
        self.client.formatter = HelpFormatter()

    # ----------------------------------------------
    # Help command that will also print hidden commands
    # ----------------------------------------------
    @commands.command(
        name='helpall',
        brief='Show this message',
        hidden=True,
    )
    @commands.guild_only()
    async def helpall(self, ctx):
        # Uncomment to always post to current channel
        # was_pm = False
        self.client.formatter = myHelpFormatter(True)
        # if self.client.pm_help:
            # self.client.pm_help = False
            # was_pm = True
        await self.client.get_command('defaulthelp').invoke(ctx)
        self.client.formatter = HelpFormatter()
        # self.client.pm_help = was_pm


def setup(client):
    client.add_cog(Help(client))
