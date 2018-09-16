import discord
import asyncio
import re
import socket
import json
import hangman.hangman as hm
from discord.ext import commands
from discord.ext.commands import Bot
import duckresponse.duckresponse as duckie

bot = commands.Bot(command_prefix='~ ', description='None')
client = discord.Client()
server = discord.Server

respond = re.compile("(r+?e+?t+?a+?r+?d+?)|(n+?i+?gg+?e+?r+?)|(f+?a+?g+?)", re.IGNORECASE)


config = json.load(open("../config.json", "r"))

respond = re.compile(".*quack.*", re.IGNORECASE)
@bot.event
async def on_message(message):
	if not message.author.bot:
		if respond.search(message.content):
			await bot.send_message(message.channel, duckie.message())
	await bot.process_commands(message)

@bot.command(pass_context=True)
async def hangman(ctx):
	hidden = hm.hangman(ctx.message.server.id, ctx.message.channel.name)
	if hidden == hm.GAMEACTIVE:
		await bot.say("A game is already active in this chat.")
		return
	embed = discord.Embed(title="Duckie hangman",
			description="Thank you for playing Duckie hang man, inspired by akaeddy#3508\n"\
			+ "your word is: " + " ".join(hidden) + "\nyou have 6 mess ups\n\npotential"\
				+ " points for this word: %d" % (hm.getPotPoints(ctx.message.server.id, ctx.message.channel.name)),
			 color=0x801680)
	await bot.say(embed=embed)

@bot.command(pass_context=True)
async def letter(ctx):
	letter = ""
	try:
		letter = ctx.message.content.split(" ")[2][0].lower()
	except Exception as e:
		await bot.say("quaaaack quack?")
		return
	err = hm.play(ctx.message.server.id, ctx.message.channel.name, letter,
					ctx.message.author.id)
	if err < 0:
		if err == hm.LOSTGAME:
			await bot.say("You've lost, the word was " + hm.getWord(ctx.message.server.id,\
				ctx.message.channel.name))
		if err == hm.ERRORNOGAME:
			await bot.say("you need to start a game quaaaack.")
		if err == hm.ERRORGAMECOMP:
			reply = "already solved; the word was " + hm.getWord(ctx.message.server.id, ctx.message.channel.name)
			await bot.say(reply)
		if err == hm.ERRORINVALID:
			await bot.say("quaaaack quack? quack")
		if err == hm.ERRORDUP:
			await bot.say("You've already tried that letter!! Quack")
		return
	elif err == hm.WONGAME:
		await bot.say("Nice you won!!! The word was " + hm.getWord(ctx.message.server.id,\
			ctx.message.channel.name))
		return


	guessesr = hm.getRightLetters(ctx.message.server.id, ctx.message.channel.name)
	guessesw = hm.getWrongLetters(ctx.message.server.id, ctx.message.channel.name)
	tries = hm.getTries(ctx.message.server.id, ctx.message.channel.name)
	guess = hm.getGuess(ctx.message.server.id, ctx.message.channel.name)

	embed = discord.Embed(title="Duckie hangman",
		description="your word is: " + " ".join(guess) + "\nyou have "\
		+ "%d" % (tries) + " mess ups\n\n"\
		+ "incorrect: " + guessesw + "\n"\
		+ "correct: " + guessesr ,
		color=0x801680)
	await bot.say(embed=embed)

@bot.command(pass_context=True, description="")
async def highscores(ctx):
	names = hm.topten(ctx.message.server.id)
	embed = discord.Embed(title="Duckie hangman", description="Highscores, top ten values!", color=0x161680)

	if (len(names) == 0):
		await bot.say("There are no highscores to display")
		return;

	namesdata = ""
	scoresdata = ""
	i = 1
	for n in reversed(names):
		username = ctx.message.server.get_member(n[0])
		if username != None:
			usernamestr = "%s#%s" % (username.name, username.discriminator)
			namesdata = namesdata + ("%d) " % (i) + usernamestr) + "\n"
			scoresdata = scoresdata + "\t%d\n" % n[1]
			if i == 10:
				break
			i = i + 1
		else:
			print("skipping: %s" % (n[0]))

	embed.add_field(name="score", value=scoresdata, inline=True)
	embed.add_field(name="users", value=namesdata, inline=True)
	await bot.say(embed=embed)

@bot.command(pass_context=True, description="")
async def myscore(ctx):
	embed = discord.Embed(title="Duckie hangman", description="your score is... "
		+ "%d!" % (hm.myscore(ctx.message.server.id, ctx.message.author.id)), color=0x161680)
	await bot.say(embed=embed)

# This is the Background task
async def video_check():
    global prev_id
    await client.wait_until_ready()
    # gets channel through id
    channel = client.get_channel('483977658577715222')
    
    # opening file to check current video title
    file = open('prev_id.txt', 'r')
    prev_id = file.read()
    file.close()
    # main loop
    while not client.is_closed:
        # check every 10 sec only
        await asyncio.sleep(10)
        # get json for latest activity of EM through youtube api
        act = (requests.get(config["gAPIURL"])).text
        act_json = json.loads(act)
        # if the json is not empty
        if act_json["items"]:
            # check if latest activity is upload and its title is new
            if act_json["items"][0]["snippet"]["type"] == "upload" and (not act_json["items"][0]["snippet"]["title"] == prev_id):
                # for console
                print("New Video: " + act_json["items"][0]["snippet"]["title"])
                # send announcement
                await client.send_message(channel,
                                          "@everyone A new video has been uploaded! " + "https://www.youtube.com/watch?v=" +
                                          (act_json["items"][0]["snippet"]["thumbnails"]["high"]["url"].split("/"))[4])
                                          # set new title as saved title
                                          prev_id = act_json["items"][0]["snippet"]["title"]
                                          file = open('prev_id.txt', 'w')
                                          file.write(prev_id)
                                          file.close()

hm.loaddata()

bot.loop.create_task(video_check())
bot.run(config["bot_key"])
