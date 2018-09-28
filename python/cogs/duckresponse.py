"""This is a cog for a discord.py bot.
It will add duckies responses to a bot

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('duckresponse')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('cogs.duckresponse')

"""

from discord.ext import commands
import random
import re


class DuckResponse():
    def __init__(self, client):
        self.client = client

    def message(self):
        intro = ["Ghost of duckie... Quack",
                 "Ghost of duckie... QUACK", "Ghost of duckie... Quaaack"]
        body = ["quack", "quuuaaack", "quack quack", "qua...", "quaack"]
        ending = [" qua...", " quack!", " quack!!", " qua..?", "..?", " quack?",
                  "...Quack?", " quack :slight_smile:", " Quack??? :thinking:",
                  " QUAACK!! :angry:"]
        numintro = len(intro)
        numbody = len(body)
        numend = len(ending)

        ret = intro[random.randint(0, numintro - 1)]
        for _ in range(0, random.randint(1, 5)):
            ret = ret + " " + body[random.randint(0, numbody - 1)]

        temp = random.randint(0, numend - 1)
        if temp == numend - 1:
            ret = ret + ending[random.randint(0, numend - 1)]
        else:
            ret = ret + ending[temp]
        return ret

    async def on_message(self, msg):
        # Ignore messages sent by bots
        if msg.author.bot:
            return

        respond = re.compile(".*quack.*", re.IGNORECASE)

        if respond.search(msg.content):
            await msg.channel.send(self.message())


def setup(client):
    client.add_cog(DuckResponse(client))
