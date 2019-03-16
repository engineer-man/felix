"""This is a cog for a discord.py bot.
It will add some responses to a bot

Commands:
    N/A

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('duckresponse')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('cogs.duckresponse')
"""

from discord.ext import commands
from discord import Embed
from datetime import datetime as dt
import random
import re
import requests
import json


with open("../config.json", "r") as conffile:
    config = json.load(conffile)

class Responses(commands.Cog):
    def __init__(self, client):
        self.client = client

    def get_quack_string(self):
        intro = ['Ghost of duckie... Quack', 'Ghost of duckie... QUACK',
                 'Ghost of duckie... Quaaack']
        body = ['quack', 'quuuaaack', 'quack quack', 'qua...', 'quaack']
        ending = ['qua...', 'quack!', 'quack!!', 'qua..?', '..?', 'quack?',
                  '...Quack?', 'quack :slight_smile:', 'Quack??? :thinking:',
                  'QUAACK!! :angry:']
        ret = [random.choice(intro)]
        for _ in range(random.randint(1, 5)):
            ret.append(random.choice(body))
        ret.append(random.choice(3 * ending[:-1] + ending[-1:]))
        return ' '.join(ret)

    def get_year_string(self):
        now = dt.now()
        year_end = dt(now.year+1, 1, 1)
        year_start = dt(now.year, 1, 1)
        year_percent = (now - year_start) / (year_end - year_start) * 100
        return f'For your information, the year is {year_percent:.1f}% over!'

    def gif_url(self, terms):
        try:
            gifs = requests.get(f'http://api.giphy.com/v1/gifs/search?api_key={config["giphy_key"]}&q=\
                {terms}&limit=20&rating=R&lang=en').json()  # offset is 0 by default

            data = random.choice([[gifs['data'][i]['title'],
                gifs['data'][i]['images']['original']['url']] for i in range(len(gifs['data']))])

            title, gif = data[0], data[1]
            return title, gif
        except IndexError:  # for when no results are returned
            pass


    @commands.Cog.listener()
    async def on_message(self, msg):
        # Ignore messages sent by bots
        if msg.author.bot:
            return

        if re.search(r'(?i).*quack.*', msg.content):
            await msg.channel.send(self.get_quack_string())

        if re.search(r'(?i).*what a twist.*', msg.content):
            await msg.channel.send('` - directed by M. Night Shyamalan.`')

        if re.search(
            r'(?i)(the|this) (current )?year is ' +
            r'((almost|basically) )?(over|done|finished)',
            msg.content
        ):
            await msg.channel.send(self.get_year_string())

        if re.search(
            r'(?i)send bobs and vagene',
            msg.content
        ):
            await msg.channel.send('😏 *sensible chuckle*')

    @commands.command(
        name='gif-embed',
        brief='Dispalys a specified gif',
        aliases=['jif', 'embed-gif'],
        hidden=True
    )
    async def gif_embed(self, ctx, *, gif):
        g = self.gif_url(gif)
        if g == None:
            await ctx.send(f'Sorry <@{ctx.message.author.id}>, no gifs found 😔')
            await ctx.message.add_reaction('❌')
        else:
            e = Embed(title=g[0], color=0x000000)
            e.set_image(url=g[1])
            e.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)

            await ctx.send(embed=e)
            await ctx.message.add_reaction('✅')

    @gif_embed.error
    async def info_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Name the gif you want next time pls')
            await ctx.message.add_reaction('❌')

def setup(client):
    client.add_cog(Responses(client))
