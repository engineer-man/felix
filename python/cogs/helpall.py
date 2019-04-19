"""This is a cog for a discord.py bot.
It adds 1 command

    helpall     show all commands (including all hidden ones)

    The commands will output to the current channel or to a dm channel
    according to the pm_help kwarg of the bot.

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from discord.ext.commands import DefaultHelpCommand
from os import path
import itertools


# Custom Help Command Class - mostly copied from ext/commands/help.py
class myHelpCommand(DefaultHelpCommand):
    # Special Help Formatter that can take a showHidden
    # Parameter to include include hidden commands
    # Mostly copied from discord.py/discord/ext/commands/formatter.py
    def __init__(self):
        super().__init__()
        self.show_hidden = False
        self.hidden = True
        self.name = 'defaulthelp'

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        # nocat = '\u200b{0.no_category}:'.format(self)
        def get_category(command, *, no_category='Help:'):
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = sorted(
                commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_indented_commands(
                commands, heading=category, max_size=max_size)

        # Node Commands
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
                        num_spaces = max_size - len(c) + 1
                        self.paginator.add_line('  ' + c + ' '*num_spaces + d)
                    else:
                        self.paginator.add_line(line + ':')
                # if helpall was called - also print the mod only part
                if self.show_hidden:
                    for line in node_help_mod:
                        if ':' in line:
                            c, d = line.split(':')
                            num_spaces = max_size - len(c) + 1
                            self.paginator.add_line(
                                '  ' + c + ' '*num_spaces + d)
                        else:
                            self.paginator.add_line(line + ':')

        except FileNotFoundError as e:
            print('node_help.txt not found', e)

        # End of Node Commands

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()

    async def send_group_help(self, group):
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)

        # if filtered:
        #     note = self.get_ending_note()
        #     if note:
        #         self.paginator.add_line()
        #         self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog):
        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)

        # note = self.get_ending_note()
        # if note:
        #     self.paginator.add_line()
        #     self.paginator.add_line(note)

        await self.send_pages()


# Help COG
class Help(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.help_command = myHelpCommand()
        self.client.get_command('help').hidden = True
        self.permitted_roles = self.client.permissions(path.dirname(__file__))['helpall']

    async def cog_check(self, ctx):
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    def cog_unload(self):
        self.client.help_command = DefaultHelpCommand()

    @commands.command(
        name='helpall',
        brief='Show this message',
        hidden=True
    )
    @commands.guild_only()
    async def helpall(self, ctx):
        self.client.help_command.show_hidden = True
        await self.client.get_command('help').invoke(ctx)
        self.client.help_command.show_hidden = False


def setup(client):
    client.add_cog(Help(client))
