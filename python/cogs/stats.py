"""This is a cog for a discord.py bot.
It adds some commands to print youtube / discord stats

Commands:
    stats           print yt subs + discord members
     ├ users        print stats about discord members
     └ channels     print stats about discord channels

Only users that have an admin role can use the commands.
"""

import json
import time
import typing
from datetime import datetime, timedelta

from discord.ext import commands
from discord import Member


class Stats(commands.Cog, name='Stats'):
    def __init__(self, client):
        self.client = client
        self.last_time = self.load_stats()

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    def load_state(self):
        with open("../state.json", "r") as statefile:
            return json.load(statefile)

    def load_stats(self):
        state = self.load_state()
        stats = state.get('stats', dict())
        if not isinstance(stats, dict):
            stats = dict()
        return stats

    def save_stats(self, stats):
        state = self.load_state()
        state['stats'] = stats
        with open("../state.json", "w") as statefile:
            return json.dump(state, statefile, indent=1)

    @commands.group(
        invoke_without_command=True,
        hidden=True,
    )
    async def stats(self, ctx):
        """Print member numbers"""
        #await ctx.trigger_typing()
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

        now = datetime.now().isoformat()
        yesterday = (datetime.now()-timedelta(seconds=60 * 60 * 24)).isoformat()
        piston_url = f'https://emkc.org/api/v1/stats/piston/usage?start={yesterday}&end={now}'
        async with self.client.session.get(piston_url) as response:
            piston_count = (await response.json()).get('count', 0)

        piston_url += '&category=bot'
        async with self.client.session.get(piston_url) as response:
            piston_bot_count = (await response.json()).get('count', 0)

        time_diff = int((time.time() - self.last_time.get('time', -1)) // 60)
        disc_diff = disc_members - self.last_time.get('disc', 0)
        subs_diff = subs - self.last_time.get('subs', 0)
        vids_diff = vids - self.last_time.get('vids', 0)
        views_diff = views - self.last_time.get('views', 0)
        piston_diff = piston_count - self.last_time.get('piston_count', 0)
        bot_diff = piston_bot_count - self.last_time.get('piston_bot_count', 0)

        self.last_time = {
            'time': time.time(),
            'disc': disc_members,
            'subs': subs,
            'vids': vids,
            'views': views,
            'piston_count': piston_count,
            'piston_bot_count': piston_bot_count,
        }
        self.save_stats(self.last_time)

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
            '\n\nPiston stats:'
            f'\nIRunCode calls/day: [{piston_bot_count}] '
            f'{"+ " if bot_diff > 0 else ""}',
            f'{str(bot_diff).replace("-", "- ") * bool(bot_diff)}',
            f'\nTotal calls/day:    [{piston_count}] '
            f'{"+ " if piston_diff > 0 else ""}',
            f'{str(piston_diff).replace("-", "- ") * bool(piston_diff)}',
            f'````last run: ',
            f'{(str(time_diff) + " minutes ago") if time_diff >= 0 else "N/A"}`'
        ]
        await ctx.send(''.join(response))

    @stats.command()
    async def users(
        self,
        ctx,
        n: typing.Optional[int] = 30
    ):
        """Show top users by messages for past n days"""
        #await ctx.trigger_typing()
        params = {
            'start': (datetime.utcnow() - timedelta(days=n)).isoformat(),
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

    @stats.command()
    async def channels(
        self, ctx,
        user: Member = None,
        n: typing.Optional[int] = 30,
    ):
        """Show top channels by messages for past n days"""
        #await ctx.trigger_typing()
        try:
            params = {
                'start': (datetime.utcnow() - timedelta(days=n)).isoformat(),
                'limit': 25,
            }
        except OverflowError:
            return

        if user:
            params['discord_id'] = user.id

        url = 'https://emkc.org/api/v1/stats/discord/channels'
        async with self.client.session.get(url, params=params) as response:
            res = await response.json()

        padding = max([len(i['channel']) for i in res])

        formatted = [
            i['channel'].ljust(padding + 2) + str(i['messages']) for i in res
        ]

        await ctx.send('```css\n' + '\n'.join(formatted) + '```')

    @stats.command()
    async def uptime(self, ctx):
        """Show felix uptime from timedelta"""
        uptime = str(datetime.now() - self.client.felix_start)
        await ctx.send(f'```{uptime[:-7]}```')


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Stats(client))
