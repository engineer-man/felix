import discord
import json
import hangman.hangman as hm
from discord.ext import commands
from discord.ext.commands import Bot

bot = Bot(command_prefix='~ ', description='None')
config = json.load(open("../config.json", "r"))

STARTUP_EXTENSIONS = ['cogs.duckresponse']
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
	if message.content in '++':
		await bot.close()
	await bot.process_commands(message)

# @bot.command(pass_context=True)
# async def hangman(ctx):
# 	hidden = hm.hangman(ctx.message.server.id, ctx.message.channel.name)
# 	if hidden == hm.GAMEACTIVE:
# 		await bot.say("A game is already active in this chat.")
# 		return
# 	embed = discord.Embed(title="Duckie hangman",
# 			description="Thank you for playing Duckie hang man, inspired by akaeddy#3508\n"\
# 			+ "your word is: " + " ".join(hidden) + "\nyou have 6 mess ups\n\npotential"\
# 				+ " points for this word: %d" % (hm.getPotPoints(ctx.message.server.id, ctx.message.channel.name)),
# 			 color=0x801680)
# 	await bot.say(embed=embed)

# @bot.command(pass_context=True)
# async def letter(ctx):
# 	letter = ""
# 	try:
# 		letter = ctx.message.content.split(" ")[2][0].lower()
# 	except Exception as e:
# 		await bot.say("quaaaack quack?")
# 		return
# 	err = hm.play(ctx.message.server.id, ctx.message.channel.name, letter,
# 					ctx.message.author.id)
# 	if err < 0:
# 		if err == hm.LOSTGAME:
# 			await bot.say("You've lost, the word was " + hm.getWord(ctx.message.server.id,\
# 				ctx.message.channel.name))
# 		if err == hm.ERRORNOGAME:
# 			await bot.say("you need to start a game quaaaack.")
# 		if err == hm.ERRORGAMECOMP:
# 			reply = "already solved; the word was " + hm.getWord(ctx.message.server.id, ctx.message.channel.name)
# 			await bot.say(reply)
# 		if err == hm.ERRORINVALID:
# 			await bot.say("quaaaack quack? quack")
# 		if err == hm.ERRORDUP:
# 			await bot.say("You've already tried that letter!! Quack")
# 		return
# 	elif err == hm.WONGAME:
# 		await bot.say("Nice you won!!! The word was " + hm.getWord(ctx.message.server.id,\
# 			ctx.message.channel.name))
# 		return


# 	guessesr = hm.getRightLetters(ctx.message.server.id, ctx.message.channel.name)
# 	guessesw = hm.getWrongLetters(ctx.message.server.id, ctx.message.channel.name)
# 	tries = hm.getTries(ctx.message.server.id, ctx.message.channel.name)
# 	guess = hm.getGuess(ctx.message.server.id, ctx.message.channel.name)

# 	embed = discord.Embed(title="Duckie hangman",
# 		description="your word is: " + " ".join(guess) + "\nyou have "\
# 		+ "%d" % (tries) + " mess ups\n\n"\
# 		+ "incorrect: " + guessesw + "\n"\
# 		+ "correct: " + guessesr ,
# 		color=0x801680)
# 	await bot.say(embed=embed)

# @bot.command(pass_context=True, description="")
# async def highscores(ctx):
# 	names = hm.topten(ctx.message.server.id)
# 	embed = discord.Embed(title="Duckie hangman", description="Highscores, top ten values!", color=0x161680)

# 	if (len(names) == 0):
# 		await bot.say("There are no highscores to display")
# 		return;

# 	namesdata = ""
# 	scoresdata = ""
# 	i = 1
# 	for n in reversed(names):
# 		username = ctx.message.server.get_member(n[0])
# 		if username != None:
# 			usernamestr = "%s#%s" % (username.name, username.discriminator)
# 			namesdata = namesdata + ("%d) " % (i) + usernamestr) + "\n"
# 			scoresdata = scoresdata + "\t%d\n" % n[1]
# 			if i == 10:
# 				break
# 			i = i + 1
# 		else:
# 			print("skipping: %s" % (n[0]))

# 	embed.add_field(name="score", value=scoresdata, inline=True)
# 	embed.add_field(name="users", value=namesdata, inline=True)
# 	await bot.say(embed=embed)

# @bot.command(pass_context=True, description="")
# async def myscore(ctx):
# 	embed = discord.Embed(title="Duckie hangman", description="your score is... "
# 		+ "%d!" % (hm.myscore(ctx.message.server.id, ctx.message.author.id)), color=0x161680)
# 	await bot.say(embed=embed)


hm.loaddata()
bot.run(config["bot_key"])
