"""Felix Discord Bot

This file starts the bot and loads all extensions/cogs and configs/permissions
The Bot automatically tries to load all extensions found in the "cogs/" folder
plus the hangman.hangman extension.

An extension can be reloaded without restarting the bot.
The extension "management" provides the commands to load/unload other extensions

This bot requires discord.py
    pip install -U discord.py
"""
from discord.ext.commands import Bot, when_mentioned_or
from discord import DMChannel
from aiohttp import ClientSession
from os import path, listdir
import json


class Felix(Bot):
    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.session = None
        with open('../config.json') as conffile:
            self.config = json.load(conffile)
        with open('./cogs/permissions.json') as permfile:
            self.permissions = json.load(permfile)
        self.last_error = None

    async def start(self, *args, **kwargs):
        self.session = ClientSession()
        await super().start(self.config["bot_key"], *args, **kwargs)

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

    def is_superuser(self, author):
        superusers = self.config['superusers']
        return author.id in superusers


client = Felix(
    command_prefix=when_mentioned_or('felix ', 'Felix '),
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
    client.main_guild = client.get_guild(473161189120147456) or client.guilds[0]
    print('Felix-Python started successfully')
    print('Active in these guilds/servers:')
    [print(g.name) for g in client.guilds]
    print('Main guild:', client.main_guild.name)
    return True


@client.event
async def on_message(message):
    if isinstance(message.channel, DMChannel):
        return
    if client.user_is_ignored(message.author):
        return
    await client.process_commands(message)


client.run()
print('Felix-Python has exited')
