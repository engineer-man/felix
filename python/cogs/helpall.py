"""This is a cog for a discord.py bot.
It hides the help command and adds these commands:

    helpall     show all commands (including all hidden ones)

    The commands will output to the current channel or to a dm channel
    according to the pm_help kwarg of the bot.

Only users that have an admin role can use the commands.
"""

import itertools
from discord import Embed
from discord.ext import commands
from discord.ext.commands import HelpCommand, DefaultHelpCommand

#pylint: disable=E1101


class myHelpCommand(HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.paginator = None
        self.spacer = "\u1160 "  # Invisible Unicode Character to indent lines

    async def send_pages(self, header=False, footer=False):
        destination = self.get_destination()
        embed = Embed(
            color=0x2ECC71
        )
        if header:
            embed.set_author(
                name=self.context.bot.description,
                icon_url=self.context.bot.user.display_avatar
            )
        for category, entries in self.paginator:
            embed.add_field(
                name=category,
                value=entries,
                inline=False
            )
        if footer:
            embed.set_footer(
                text='Use felix help <command/category> for more information.'
            )
        await destination.send(embed=embed)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        def get_category(command):
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else 'Help:'

        filtered = await self.filter_commands(
            bot.commands,
            sort=True,
            key=get_category
        )
        to_iterate = itertools.groupby(filtered, key=get_category)
        for cog_name, command_grouper in to_iterate:
            cmds = sorted(command_grouper, key=lambda c: c.name)
            category = f'► {cog_name}'
            if len(cmds) == 1:
                entries = f'{self.spacer}{cmds[0].name} → {cmds[0].short_doc}'
            else:
                entries = ''
                while len(cmds) > 0:
                    entries += self.spacer
                    entries += ' | '.join([cmd.name for cmd in cmds[0:8]])
                    cmds = cmds[8:]
                    entries += '\n' if cmds else ''
            self.paginator.append((category, entries))
        await self.send_pages(header=True, footer=True)

    async def send_cog_help(self, cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            await self.context.send(
                'No public commands in this cog. Try again with felix helpall.'
            )
            return
        category = f'▼ {cog.qualified_name}'
        entries = '\n'.join(
            self.spacer +
            f'**{command.name}** → {command.short_doc or command.description}'
            for command in filtered
        )
        self.paginator.append((category, entries))
        await self.send_pages(footer=True)

    async def send_group_help(self, group):
        filtered = await self.filter_commands(group.commands, sort=True)
        if not filtered:
            await self.context.send(
                'No public commands in group. Try again with felix helpall.'
            )
            return
        category = f'**{group.name}** - {group.description or group.short_doc}'
        entries = '\n'.join(
            self.spacer + f'**{command.name}** → {command.short_doc}'
            for command in filtered
        )
        self.paginator.append((category, entries))
        await self.send_pages(footer=True)

    async def send_command_help(self, command):
        signature = self.get_command_signature(command)
        helptext = command.help or command.description or 'No help Text'
        self.paginator.append(
            (signature,  helptext)
        )
        await self.send_pages()

    async def prepare_help_command(self, ctx, command=None):
        self.paginator = []
        await super().prepare_help_command(ctx, command)


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.help_command = myHelpCommand(
            command_attrs={
                'aliases': ['halp'],
                'help': 'Shows help about the bot, a command, or a category'
            }
        )

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    def cog_unload(self):
        self.client.get_command('help').hidden = False
        self.client.help_command = DefaultHelpCommand()

    @commands.command(
        aliases=['halpall'],
        hidden=True
    )
    async def helpall(self, ctx, *, text=None):
        """Print bot help including all hidden commands"""
        self.client.help_command = myHelpCommand(show_hidden=True)
        if text:
            await ctx.send_help(text)
        else:
            await ctx.send_help()
        self.client.help_command = myHelpCommand()


async def setup(client):
    await client.add_cog(Help(client))
