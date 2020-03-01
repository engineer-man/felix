"""Felix Discord Bot

This file starts the bot and loads all extensions/cogs and configs/permissions
The Bot automatically tries to load all extensions found in the "cogs/" folder
plus the hangman.hangman extension.

An extension can be reloaded without restarting the bot.
The extension "management" provides the commands to load/unload other extensions

This bot requires discord.py
    pip install -U discord.py
"""
import json
from datetime import datetime
from os import path, listdir
from discord.ext.commands import Bot, when_mentioned_or
from discord import DMChannel
from aiohttp import ClientSession



class Felix(Bot):
    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.session = None
        with open('../config.json') as conffile:
            self.config = json.load(conffile)
        self.last_errors = []

    async def start(self, *args, **kwargs):
        self.session = ClientSession()
        await super().start(self.config["bot_key"], *args, **kwargs)

    async def close(self):
        await self.session.close()
        await super().close()

    def user_is_admin(self, user):
        try:
            user_roles = [role.id for role in user.roles]
        except AttributeError:
            return False
        permitted_roles = self.config['admin_roles']
        return any(role in permitted_roles for role in user_roles)

    def user_is_superuser(self, user):
        superusers = self.config['superusers']
        return user.id in superusers

    def user_is_ignored(self, user):
        user_roles = [role.id for role in user.roles]
        if self.config['ignore_role'] in user_roles:
            return True
        return False


client = Felix(
    command_prefix=when_mentioned_or('felix ', 'Felix '),
    description='Hi I am Felix!',
    max_messages=15000
)

STARTUP_EXTENSIONS = []

for file in listdir(path.join(path.dirname(__file__), 'cogs/')):
    filename, ext = path.splitext(file)
    if '.py' in ext:
        STARTUP_EXTENSIONS.append(f'cogs.{filename}')

for extension in reversed(STARTUP_EXTENSIONS):
    try:
        client.load_extension(f'{extension}')
    except Exception as e:
        client.last_errors.append((e, datetime.utcnow(), None))
        exc = f'{type(e).__name__}: {e}'
        print(f'Failed to load extension {extension}\n{exc}')


@client.event
async def on_ready():
    main_id = client.config['main_guild']
    client.main_guild = client.get_guild(main_id) or client.guilds[0]
    print('\nActive in these guilds/servers:')
    [print(g.name) for g in client.guilds]
    print('\nMain guild:', client.main_guild.name)
    print('\nFelix-Python started successfully')
    return True


@client.event
async def on_message(msg):
    if isinstance(msg.channel, DMChannel):
        return
    if client.user_is_ignored(msg.author):
        return
    await client.process_commands(msg)


client.run()
print('Felix-Python has exited')
