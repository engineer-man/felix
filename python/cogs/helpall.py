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

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from discord.ext.commands.bot import _default_help_command
from discord.ext.commands.formatter import HelpFormatter, Paginator, Command
from os import path
import json
import itertools
import inspect


class myHelpFormatter(HelpFormatter):
    # Special Help Formatter that can take a showHidden
    # Parameter to include include hidden commands
    # Mostly copied from discord.py/discord/ext/commands/formatter.py
    def __init__(self, showHidden=False, is_sub=False):
        super().__init__()
        self.show_hidden = showHidden
        self.is_sub = is_sub

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

        description = self.command.description if not self.is_cog(
        ) else inspect.getdoc(self.command)

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
            return cog + ':' if cog is not None else '\u200bDefault:'

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

        # Don't print node commands if help is called with a subcommand
        if self.is_sub:
            return self._paginator.pages

        try:
            with open('node_help.txt') as f:
                node_help = f.read().strip()
                node_help = node_help.split('\n')
                node_help_mod = []
                # Split node_help into public part and mod only part
                # the line to split at should begin with ---
                for i in range(len(node_help)):
                    if node_help[i].startswith('---'):
                        node_help_mod = node_help[i+1:]
                        node_help = node_help[0:i]
                        break
                # Print public part
                for line in node_help:
                    if ':' in line:
                        c, d = line.split(':')
                        num_spaces = max_width - len(c) + 1
                        self._paginator.add_line('  ' + c + ' '*num_spaces + d)
                    else:
                        self._paginator.add_line(line + ':')
                # if helpall was called - also print the mod only part
                if self.show_hidden:
                    for line in node_help_mod:
                        if ':' in line:
                            c, d = line.split(':')
                            num_spaces = max_width - len(c) + 1
                            self._paginator.add_line(
                                '  ' + c + ' '*num_spaces + d)
                        else:
                            self._paginator.add_line(line + ':')

        except FileNotFoundError as e:
            print('node_help.txt not found', e)
        return self._paginator.pages


def is_staff():
    """Used as a decorator for bot commands
    to make sure only staff can see/use it

    we don't use cog_checks in this cog because we have 2 different commands
    that have different role restrictions
    """
    async def predicate(ctx):
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            permitted_roles = json.load(f)[__name__.split('.')[-1]]
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in permitted_roles for role in user_roles)
    return commands.check(predicate)


class Help(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client

    # ----------------------------------------------
    # Custom help command
    # ----------------------------------------------
    @commands.command(
        name='help',
        brief='Show this message',
    )
    @commands.guild_only()
    async def newhelp(self, ctx):
        is_sub = ctx.message.content not in 'felix help '
        self.client.formatter = myHelpFormatter(False, is_sub)
        await self.client.get_command('defaulthelp').invoke(ctx)
        self.client.formatter = HelpFormatter()

    # ----------------------------------------------
    # Helpall command that will also print hidden commands
    # ----------------------------------------------
    @commands.command(
        name='helpall',
        brief='Show this message',
        hidden=True,
    )
    @commands.guild_only()
    @is_staff()
    async def helpall(self, ctx):
        is_sub = ctx.message.content not in 'felix helpall '
        self.client.formatter = myHelpFormatter(True, is_sub)
        await self.client.get_command('defaulthelp').invoke(ctx)
        self.client.formatter = HelpFormatter()


def setup(client):
    client.add_cog(Help(client))
