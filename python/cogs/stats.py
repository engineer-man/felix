"""This is a cog for a discord.py bot.
It adds some commands to print youtube / discord stats

Commands:
    stats         print yt subs + discord members
     ├ users        print stats about discord members
     └ channels     print stats about discord channels

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from discord import Member
from os import path
from datetime import datetime, timedelta
import json
import time
import typing


class Stats(commands.Cog, name='Stats'):
    def __init__(self, client):
        self.client = client
        self.last_time = self.load_stats()
        self.permitted_roles = self.client.permissions(path.dirname(__file__))['stats']

    async def cog_check(self, ctx):
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    def load_state(self):
        with open("../state.json", "r") as statefile:
            return json.load(statefile)

    def load_stats(self):
        state = self.load_state()
        return state.get('stats', [])

    def save_stats(self, stats):
        state = self.load_state()
        state['stats'] = stats
        with open("../state.json", "w") as statefile:
            return json.dump(state, statefile, indent=1)

    @commands.group(
        invoke_without_command=True,
        name='stats',
        brief='Print member numbers',
        description='Print the number of YouTube subs and Discord members',
        hidden=True,
    )
    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def stats(self, ctx):
        await ctx.trigger_typing()
        url = ('https://www.googleapis.com/youtube/v3/channels'
               '?part=statistics'
               '&id=UCrUL8K81R4VBzm-KOYwrcxQ'
               f'&key={self.client.config["yt_key"]}')
        async with self.client.session.get(url) as response:
            r = await response.json()
        statistics = r['items'][0]['statistics']
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
        self.save_stats(self.last_time)

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

    @stats.command(
        name='users',
        brief='User message stats',
        description='Show top users by messages for past n days'
    )
    @commands.guild_only()
    async def users(self, ctx, n: typing.Optional[int] = 30):
        await ctx.trigger_typing()
        params = {
            'start': (datetime.now() - timedelta(days=n)).isoformat(),
            'limit': 25,
        }

        url = 'https://emkc.org/api/v1/stats/discord/messages'
        async with self.client.session.get(url, params=params) as response:
            res = await response.json()

        padding = max([len(i['user']) for i in res])

        formatted = [
            i['user'].ljust(padding + 2) + str(i['messages']) for i in res
        ]

        await ctx.send('```css\n' + '\n'.join(formatted) + '```')

    @stats.command(
        name='channels',
        brief='Channel message stats',
        description='Show top channels by messages for past n days'
    )
    @commands.guild_only()
    async def channels(
        self, ctx,
        n: typing.Optional[int] = 30,
        user: Member = None
    ):
        await ctx.trigger_typing()
        params = {
            'start': (datetime.now() - timedelta(days=n)).isoformat(),
            'limit': 25,
        }

        if user:
            params['user'] = str(user)

        url = 'https://emkc.org/api/v1/stats/discord/channels'
        async with self.client.session.get(url, params=params) as response:
            res = await response.json()

        padding = max([len(i['channel']) for i in res])

        formatted = [
            i['channel'].ljust(padding + 2) + str(i['messages']) for i in res
        ]

        await ctx.send('```css\n' + '\n'.join(formatted) + '```')


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Stats(client))
