"""Python version of Felix

This file only starts the bot and loads all extensions/cogs
New extensions have to be added to STARTUP_EXTENSIONS to be loaded automatically

An extension can be reloaded without restarting the bot.
The extension "management" provides the commands to load/unload other extensions

This bot requires discord.py rewrite
pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py
"""


import json
from discord.ext.commands import Bot

bot = Bot(command_prefix=('felix ', '~ ', 'felixtest '),
          description='Hi I am Felix!',
          help_attrs={'name': 'defaulthelp', 'hidden': True},
          )
config = json.load(open("../config.json", "r"))

STARTUP_EXTENSIONS = [
    'hangman.hangman',
    'cogs.duckresponse',
    'cogs.inviteblocker',
    'cogs.management',
    'cogs.helpall',
    'cogs.poll',
    'cogs.chatlog'
]
for extension in STARTUP_EXTENSIONS:
    try:
        bot.load_extension(f'{extension}')
    except Exception as e:
        exc = f'{type(e).__name__}: {e}'
        print(f'Failed to load extension {extension}\n{exc}')


@bot.event
async def on_ready():
    print('Felix-Python started successfully')
    return True


@bot.event
async def on_message(message):
    await bot.process_commands(message)


bot.run(config["bot_key"])
print('Felix-Python has exited')
