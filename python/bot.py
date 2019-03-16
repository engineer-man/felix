"""Python version of Felix

This file only starts the bot and loads all extensions/cogs
The Bot automatically tries to load all extensions found in the "cogs/" folder
plus the hangman.hangman extension.

An extension can be reloaded without restarting the bot.
The extension "management" provides the commands to load/unload other extensions

This bot requires discord.py rewrite
pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py
pip install requests
"""
from discord.ext.commands import Bot, CommandOnCooldown
import json
import os
import sys
import traceback

with open("../config.json", "r") as conffile:
    config = json.load(conffile)

bot = Bot(command_prefix=('felix ', '~ '),
          description='Hi I am Felix!',
          max_messages=15000
          )

STARTUP_EXTENSIONS = ['hangman.hangman']

for file in os.listdir(os.path.join(os.path.dirname(__file__), 'cogs/')):
    filename, ext = os.path.splitext(file)
    if '.py' in ext:
        STARTUP_EXTENSIONS.append(f'cogs.{filename}')

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


@bot.event
async def on_command_error(ctx, exception):
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

    print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
    traceback.print_exception(
        type(exception), exception, exception.__traceback__, file=sys.stderr
    )

bot.run(config["bot_key"])
print('Felix-Python has exited')
