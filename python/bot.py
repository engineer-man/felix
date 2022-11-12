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
from datetime import datetime, timezone
from os import path, listdir
from discord.ext.commands import AutoShardedBot, when_mentioned_or, Context
from discord import DMChannel, Intents, AllowedMentions, Status
from aiohttp import ClientSession, ClientTimeout


class Felix(AutoShardedBot):
    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.main_guild = None
        self.session = None
        self.flood_mode = False
        self.felix_start = datetime.now()
        self.status = Status.online
        with open('../config.json') as conffile:
            self.config = json.load(conffile)
        self.last_errors = []

    async def start(self, *args, **kwargs):
        self.session = ClientSession(timeout=ClientTimeout(total=30))
        await super().start(*args, **kwargs)

    async def close(self):
        await self.session.close()
        await super().close()

    async def setup_hook(self):
        print('Loading Extensions:')
        STARTUP_EXTENSIONS = []
        for file in listdir(path.join(path.dirname(__file__), 'cogs/')):
            filename, ext = path.splitext(file)
            if '.py' in ext:
                STARTUP_EXTENSIONS.append(f'cogs.{filename}')

        for extension in reversed(STARTUP_EXTENSIONS):
            try:
                print('loading', extension)
                await self.load_extension(f'{extension}')
            except Exception as e:
                await self.log_error(e, 'Cog INIT')
                exc = f'{type(e).__name__}: {e}'
                print(f'Failed to load extension {extension}\n{exc}')

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

    async def log_error(self, error, error_source=None):
        is_context = isinstance(error_source, Context)
        has_attachment = bool(error_source.message.attachments) if is_context else False
        self.last_errors.append((
            error,
            datetime.now(tz=timezone.utc),
            error_source,
            error_source.message.content if is_context else None,
            error_source.message.attachments[0] if has_attachment else None,
        ))
        self.status = Status.dnd
        activity = self.main_guild.me.activity if self.main_guild else None
        await self.change_presence(status=self.status, activity=activity)

client = Felix(
    command_prefix=when_mentioned_or('felix ', 'Felix '),
    description='Hi I am Felix!',
    max_messages=15000,
    intents=Intents.all(),
    allowed_mentions=AllowedMentions(everyone=False, users=True, roles=True)
)

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
    await client.log_error(sys.exc_info()[1], 'DEFAULT HANDLER:' + event_method)


@client.event
async def on_message(msg):
    # Ignore DMs
    if isinstance(msg.channel, DMChannel):
        return
    await client.process_commands(msg)


client.run(client.config['bot_key'])
print('Felix-Python has exited')
