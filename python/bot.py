"""Python version of Felix

This file only starts the bot and loads all extensions/cogs
The Bot automatically tries to load all extensions found in the "cogs/" folder
plus the hangman.hangman extension.

An extension can be reloaded without restarting the bot.
The extension "management" provides the commands to load/unload other extensions

This bot requires discord.py rewrite
pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py
"""
from discord.ext.commands import Bot, CommandOnCooldown, MissingRequiredArgument
import json
import os
import sys
import traceback
from aiohttp import ClientSession


class FelixBot(Bot):
    def __init__(self):
        super().__init__(
            command_prefix=('felix ', '~ '),
            description='Hi I am Felix!',
            max_messages=15000
        )
        self.session = ClientSession(loop=self.loop)
        with open("../config.json", "r") as conffile:
            self.config = json.load(conffile)
        self.STARTUP_EXTENSIONS = ['hangman.hangman']

    def permissions(self, location):
        with open(os.path.join(location, 'permissions.json')) as f:
            permitted_roles = json.load(f)
        return permitted_roles

    async def modules(self):
        for file in os.listdir(os.path.join(os.path.dirname(__file__), 'cogs/')):
            filename, ext = os.path.splitext(file)
            if '.py' in ext:
                self.STARTUP_EXTENSIONS.append(f'cogs.{filename}')

        for extension in self.STARTUP_EXTENSIONS:
            try:
                self.load_extension(f'{extension}')
            except Exception as e:
                exc = f'{type(e).__name__}: {e}'
                print(f'Failed to load extension {extension}\n{exc}')

    async def on_ready(self):
        await self.modules()
        print('Felix-Python started successfully')
        return True

    async def on_message(self, message):
        await self.process_commands(message)

    async def on_command_error(self, ctx, exception):
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

        print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
        traceback.print_exception(
            type(exception), exception, exception.__traceback__, file=sys.stderr
        )

    def run(self):
        super().run(self.config["bot_key"])


if __name__ == "__main__":
    FelixBot().run()

print('Felix-Python has exited')
