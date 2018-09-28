import discord
import json
from discord.ext import commands
from discord.ext.commands import Bot

bot = Bot(command_prefix=('felix ','+ '), description='None')
config = json.load(open("../config.json", "r"))

STARTUP_EXTENSIONS = ['cogs.duckresponse.duckresponse',
                      'cogs.inviteblocker',
                      'hangman.hangman']
for extension in STARTUP_EXTENSIONS:
	try:
		bot.load_extension(f'{extension}')
	except Exception as e:
		exc = f'{type(e).__name__}: {e}'
		print(f'Failed to load extension {extension}\n{exc}')


@bot.event
async def on_ready():
    # This is just for debugging
    app_info = await bot.application_info()
    await app_info.owner.send(
        'Ready\n'
        + f'```css\nLoaded extensions:'
        + f' {[e for e in bot.extensions]}```')
    return True


@bot.event
async def on_message(message):
    if message.content in '+quit':
        await bot.close()
    await bot.process_commands(message)


bot.run(config["bot_key"])
pass
