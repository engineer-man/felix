import discord
import asyncio
import requests
import json
from discord.ext import commands
from discord.ext.commands import Bot

bot = commands.Bot(command_prefix='codit ', description='None')
client = discord.Client()
server = discord.Server

lexicon = json.load(open("./lexicon.json", "r"))
config = json.load(open("../config.json", "r"))

@bot.command(pass_context=True)
async def using(ctx):
	print(ctx.message.content + "\n\n")
	langdata = ctx.message.content[12:]
	data = getCode(langdata)
	lang = getLang(langdata).rstrip().lstrip()
	if lang == None:
		await bot.say("the language you chosen was invalid.")
		return
	if lang not in lexicon:
		await bot.say("that language was not in the lexicon.\n"\
		"type 'codit helpme' if you'd like help.")
		return
	if data == None:
		await bot.say("the format to your code block might have "\
					  "been a bit off. "\
					  "type 'codit helpme' if you're looking for assistance.")
		return
	output = runCode(lang, data)
	output = (output).split("\n")
	if (len(output) > 25):
		await bot.say(("```" + ("\n".join(output[:25])))[:400] + "\n...\n ```")
	else:
		await bot.say(("```" + ("\n".join(output)))[:400] + " ```")


def getCode(data):
	try:
		data = data.split("```")[1]
		data = "\n".join(data.split('\n')[1:-1])
		return data
	except Exception as e:
		return None

def getLang(data):
	try:
		return data.split('\n')[0]
	except Exception as e:
		return None

@bot.command(pass_context=True)
async def helpme(ctx):
	pstr = "to use the codit feature type\n"\
		   "codit using <lang>\n"\
		   "\`\`\`\n"\
		   "Your code here\n"\
		   "\`\`\`\n"\
		   "each langs are as follows:\n"\
		   "```<lang>\n"
	for name in lexicon:
		pstr = pstr + "%-10s\n" % (name)
	pstr = pstr + "```"
	await bot.say(pstr)

def runCode(codetype, code):
	print(codetype)
	print(code)
	apidata = {"language":codetype, "source":code}
	response = requests.post(url=config["apiurl"], data=apidata, headers={'Authorization': config["apikey"]})
	response = json.loads(response.text)
	print(response)
	if response["status"] == "ok":
		return response["payload"]["output"]


#data = {"language":"python3", "source":"print(\"hello\")"}
#response = requests.post(url=config["apiurl"], data=data, headers={'Authorization': config["apikey"]})
#print(json.loads(response.text))
bot.run(config["bot_key"])
