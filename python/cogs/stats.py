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
import time

with open("../config.json", "r") as conffile:
    config = json.load(conffile)


class Stats():
    def __init__(self, client):
        self.client = client
        self.last_time = []

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
        subs = int(statistics['subscriberCount'])
        vids = int(statistics['videoCount'])
        views = int(statistics['viewCount'])
        disc_members = ctx.channel.guild.member_count

        time_diff, disc_diff, subs_diff, vids_diff, views_diff = -1, 0, 0, 0, 0
        if self.last_time:
            time_diff = int((time.time() - self.last_time[0]) // 60)
            disc_diff = disc_members - self.last_time[1]
            subs_diff = subs - self.last_time[2]
            vids_diff = vids - self.last_time[3]
            views_diff = views - self.last_time[4]

        self.last_time = [time.time(), disc_members, subs, vids, views]

        # What an abomination
        response = [
            '```css',
            f'\nDiscord members: [{disc_members}] ',
            f'{"+ " if disc_diff > 0 else ""}',
            f'{str(disc_diff).replace("-", "- ") * bool(disc_diff)}',
            f'\nYouTube subs:    [{subs}] ',
            f'{"+ " if subs_diff > 0 else ""}',
            f'{str(subs_diff).replace("-", "- ") * bool(subs_diff)}',
            f'\nYouTube videos:  [{vids}] ',
            f'{"+ " if vids_diff > 0 else ""}',
            f'{str(vids_diff).replace("-", "- ") * bool(vids_diff)}',
            f'\nYouTube views:   [{views}] '
            f'{"+ " if views_diff > 0 else ""}',
            f'{str(views_diff).replace("-", "- ") * bool(views_diff)}',
            f'````last run: ',
            f'{(str(time_diff) + " minutes ago") if time_diff >= 0 else "N/A"}`'
        ]
        await ctx.send(''.join(response))


def setup(client):
    """This is called then the cog is loaded via load_extension"""
    client.add_cog(Stats(client))
