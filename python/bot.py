"""Python version of Felix

This file only starts the bot and loads all extensions/cogs
The Bot automatically tries to load all extensions found in the "cogs/" folder
plus the hangman.hangman extension.

An extension can be reloaded without restarting the bot.
The extension "management" provides the commands to load/unload other extensions

This bot requires discord.py rewrite
pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py
"""
from discord.ext.commands import Bot
import json
import os

config = json.load(open("../config.json", "r"))

bot = Bot(command_prefix=('felix ', '~ '),
          description='Hi I am Felix!',
          help_attrs={'name': 'defaulthelp', 'hidden': True},
          )

STARTUP_EXTENSIONS=['hangman.hangman']

COG_DIR = 'cogs'
for file in os.listdir(f'{COG_DIR}/'):
    filename, ext = os.path.splitext(file)
    if '.py' in ext:
        STARTUP_EXTENSIONS.append(f'{COG_DIR}.{filename}')

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
