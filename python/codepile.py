import discord
import asyncio
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
    runCode(lang, data)


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
           "\`\`\`(ignored line)\n"\
           "Your code here\n"\
           "\`\`\`\n"\
           "each langs are as follows:\n"\
           "```<lang>    |  <lang used to run>\n"
    for name in lexicon:
        pstr = pstr + "%-10s| %s\n" % (name, lexicon[name]["apilang"])
    pstr = pstr + "```"
    await bot.say(pstr)

def runCode(codetype, code):
    print(codetype)
    print(code)
    apidata = {"language":codetype, "source":code}
    ret = requests.post(url=config["apiurl"], params=apidata,\
                        headers={'Authorization': config["apikey"]})

bot.run(config["bot_key"])
