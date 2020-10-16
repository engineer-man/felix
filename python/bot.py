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
import traceback
import sys
from datetime import datetime
from os import path, listdir
from discord.ext.commands import Bot, when_mentioned_or
from discord import DMChannel, Message, Activity, Intents, AllowedMentions
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

intents = Intents.default()
intents.members = True

client = Felix(
    command_prefix=when_mentioned_or('felix ', 'Felix '),
    description='Hi I am Felix!',
    max_messages=15000,
    intents=intents,
    allowed_mentions=AllowedMentions(everyone=False, users=True, roles=True)
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
        client.last_errors.append((e, datetime.utcnow(), None, None))
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
async def on_error(event_method, *args, **kwargs):
    """|coro|

    The default error handler provided by the client.

    By default this prints to :data:`sys.stderr` however it could be
    overridden to have a different implementation.
    Check :func:`~discord.on_error` for more details.
    """
    print('Default Handler: Ignoring exception in {}'.format(event_method), file=sys.stderr)
    traceback.print_exc()
    # --------------- custom code below -------------------------------
    # Saving the error if it resulted from a message edit
    if len(args) > 1:
        a1, a2,*_ = args
        if isinstance(a1, Message) and isinstance(a2, Message):
            client.last_errors.append((sys.exc_info()[1], datetime.utcnow(), a2, a2.content))
        await client.change_presence(
            activity=Activity(name='ERROR encountered', url=None, type=3)
        )

@client.event
async def on_message(msg):
    if isinstance(msg.channel, DMChannel):
        return
    if client.user_is_ignored(msg.author):
        return
    await client.process_commands(msg)


client.run()
print('Felix-Python has exited')
