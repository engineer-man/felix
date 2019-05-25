"""Felix Discord Bot

This file starts the bot and loads all extensions/cogs and configs/permissions
The Bot automatically tries to load all extensions found in the "cogs/" folder
plus the hangman.hangman extension.

An extension can be reloaded without restarting the bot.
The extension "management" provides the commands to load/unload other extensions

This bot requires discord.py
    pip install -U discord.py
"""
from discord.ext.commands import Bot, CommandOnCooldown, MissingRequiredArgument
from discord.ext.commands import CheckFailure, when_mentioned_or
from aiohttp import ClientSession
from os import path, listdir
import json
import sys
import traceback


class Felix(Bot):
    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.session = None
        with open('../config.json') as conffile:
            self.config = json.load(conffile)
        with open('./cogs/permissions.json') as permfile:
            self.permissions = json.load(permfile)

    def run(self, *args, **kwargs):
        super().run(self.config["bot_key"], *args, **kwargs)

    async def close(self):
        await self.session.close()
        await super().close()

    def user_has_permission(self, author, module_name):
        try:
            user_roles = [role.id for role in author.roles]
        except AttributeError:
            return False
        permitted_roles = self.permissions[module_name]
        return any(role in permitted_roles for role in user_roles)

    def user_is_ignored(self, author):
        user_roles = [role.id for role in author.roles]
        if 581535776697876491 in user_roles:
            return True
        return False


client = Felix(
    command_prefix=when_mentioned_or('felix ', 'Felix ', '~ '),
    description='Hi I am Felix!',
    max_messages=15000
)

STARTUP_EXTENSIONS = ['hangman.hangman']

for file in listdir(path.join(path.dirname(__file__), 'cogs/')):
    filename, ext = path.splitext(file)
    if '.py' in ext:
        STARTUP_EXTENSIONS.append(f'cogs.{filename}')

for extension in reversed(STARTUP_EXTENSIONS):
    try:
        client.load_extension(f'{extension}')
    except Exception as e:
        exc = f'{type(e).__name__}: {e}'
        print(f'Failed to load extension {extension}\n{exc}')


@client.event
async def on_ready():
    client.session = ClientSession()
    print('Felix-Python started successfully')
    return True


@client.event
async def on_message(message):
    if client.user_is_ignored(message.author):
        return
    await client.process_commands(message)


@client.event
async def on_command_error(ctx, exception):
    if client.extra_events.get('on_command_error', None):
        return

    if hasattr(ctx.command, 'on_error'):
        return

    cog = ctx.cog
    if cog:
        attr = f'_{cog.__class__.__name__}__error'
        if hasattr(cog, attr):
            return

    if type(exception) == CommandOnCooldown:
        await ctx.author.send(exception)
        await ctx.message.delete()
        print(f'{ctx.command} on cooldown for {ctx.author}', file=sys.stderr)
        return

    if type(exception) == MissingRequiredArgument:
        par = str(exception.param)
        missing = par.split(": ")[0]
        if ':' in par:
            missing_type = ' (' + str(par).split(": ")[1] + ')'
        else:
            missing_type = ''
        await ctx.send(
            f'Missing parameter: `{missing}{missing_type}`' +
            f'\nIf you are not sure how to use the command, try running ' +
            f'`felix help {ctx.command.name}`'
        )
        return

    if type(exception) == CheckFailure:
        print(
            f'MISSING PERMISSION | USER: {ctx.author} | COMMAND: {ctx.command}'
        )
        return

    print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
    traceback.print_exception(
        type(exception), exception, exception.__traceback__, file=sys.stderr
        )

client.run()
print('Felix-Python has exited')
