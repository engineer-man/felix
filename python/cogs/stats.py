"""This is a cog for a discord.py bot.
It prints out the current number of discord members and yt subs.

Commands:
    numbers         print yt subs + discord members

Load the cog by calling client.load_extension with the name of this python file
as an argument (without .py)
    example:    bot.load_extension('example')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('folder.example')
"""

from discord.ext import commands
from discord import Embed, Color
import json
import requests

with open("../config.json", "r") as conffile:
    config = json.load(conffile)

class Stats():
    def __init__(self, client):
        self.client = client

    @commands.command(
        name='stats',
        brief='Print member numbers',
        description='Print the number of YouTube subs and Discord members',
        hidden=False,
    )
    @commands.guild_only()
    async def stats(self, ctx):
        url = ('https://www.googleapis.com/youtube/v3/channels'
               '?part=statistics'
               '&id=UCrUL8K81R4VBzm-KOYwrcxQ'
               f'&key={config["yt_key"]}')
        r = requests.get(url)
        statistics = r.json()['items'][0]['statistics']
        subs = statistics['subscriberCount']
        vids = statistics['videoCount']
        views = statistics['viewCount']
        disc_members = str(ctx.channel.guild.member_count)

        response = [
            '```css',
            f'\nDiscord members: [{disc_members}]',
            f'\nYouTube subs:    [{subs}]',
            f'\nYouTube videos:  [{vids}]',
            f'\nYouTube views:   [{views}]```'
        ]
        await ctx.send(''.join(response))

        # The following sends the information as an embed
        # description = (
        #     f'The Discord server has {disc_members} members'
        #     '\n\nThe Youtube channel has:'
        #     f'\n    {subs} Subscribers'
        #     f'\n    {vids} Videos'
        #     f'\n    {views} Total Video Views'
        #     )
        # embed = Embed(
        #     title='Stats',
        #     description=description,
        #     color=Color.dark_gold())
        # await ctx.send(embed=embed)


def setup(client):
    """This is called then the cog is loaded via load_extension"""
    client.add_cog(Stats(client))
