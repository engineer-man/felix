"""This is a cog for a discord.py bot.
It will announce if a user completed a puzzle on adventofcode.com

Commands:
    None

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('aoc')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('my_extensions.aoc')
"""

from discord.ext import commands
from datetime import datetime, timedelta
import asyncio


API_URL = 'https://adventofcode.com/2018/leaderboard/private/view/208847.json'
EM_SERVER = 473161189120147456
AOC_CHANNEL = 514527842399420427
INTERVAL = 180


class AdventOfCode(commands.Cog, name='Advent of Code'):
    def __init__(self, client):
        self.client = client
        self.cookie = {'session': self.client.config['aoc_session']}
        self.task = self.client.loop.create_task(self.aoc_monitor())
        self.members = {}

    async def aoc_monitor(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        channel = self.client.get_guild(EM_SERVER).get_channel(AOC_CHANNEL)
        async with self.client.session.get(API_URL, cookies=self.cookie) as response:
            r = await response.json()
        self.members = r['members']
        try:
            while not self.client.is_closed():
                msg = []
                async with self.client.session.get(API_URL, cookies=self.cookie) as response:
                    r = await response.json()
                current_members = r['members']
                for member, data in current_members.items():
                    if member not in self.members:
                        msg.append(
                            f"#{data['name'].replace(' ','_')} " +
                            "has just joined the leaderboard."
                        )
                        continue
                        # self.members[member] = {
                        #     'completion_day_level': {},
                        #     'stars': 0
                        # }
                    if data['stars'] == self.members[member]['stars']:
                        continue
                    new_stats = data['completion_day_level']
                    old_stats = self.members[member]['completion_day_level']
                    current_stats = set()
                    for k, v in new_stats.items():
                        for s in v.keys():
                            current_stats.add(f'{k}-{s}')
                    previous_stats = set()
                    for k, v in old_stats.items():
                        for s in v.keys():
                            previous_stats.add(f'{k}-{s}')
                    for puzzle in sorted(current_stats):
                        if puzzle not in previous_stats:
                            day, pzl = puzzle.split('-')
                            msg.append(
                                f"#{data['name'].replace(' ', '_')} " +
                                f"solved: [{day} - {pzl}]"
                            )
                if msg:
                    await channel.send(
                        '\n'.join([
                            "```css",
                            '\n'.join(msg),
                            "```"
                        ])
                    )

                self.members = current_members
                await asyncio.sleep(INTERVAL)
        except asyncio.CancelledError:
            pass

    @commands.command(
        name='aoc',
        brief='Show Advent of Code stats for a specific day',
        description='Show Advent of Code stats for a specific day' +
                    '\n(only works in #advent-of-code)',
        hidden=False,
    )
    async def aoc(self, ctx, day):
        day = day.replace('day', '')
        if not day.isdigit():
            return
        if int(day) < 1 or int(day) > 24:
            return
        if not ctx.channel.id == AOC_CHANNEL:
            return
        async with self.client.session.get(API_URL, cookies=self.cookie) as response:
            r = await response.json()
        members = r['members']
        parts = {'1': [], '2': []}
        for data in members.values():
            days = data['completion_day_level']
            if day not in days:
                continue
            d = days[day]
            for k, v in d.items():
                parts[k].append((v['get_star_ts'], data['name']))

        for p in '12':
            paginator = []
            current = parts[p]
            if not current:
                continue
            paginator.append(f'Advent of Code puzzle [{day}]|[{p}]')
            first_time = 0
            for rank, entry in enumerate(sorted(current, key=lambda x: x[0])):
                if not rank:
                    first_time = int(entry[0])
                    paginator.append(
                        f'{rank+1}.{entry[1].replace(" ","_")}'.ljust(25) +
                        f'[{datetime.fromtimestamp(first_time)}]'
                    )
                else:
                    paginator.append(
                        f'{rank+1}.{entry[1].replace(" ","_")}'.ljust(25) +
                        f'[+ {timedelta(seconds=int(entry[0]) - first_time)}]'
                    )

            if not paginator:
                return
            paginator.insert(0, f'```css')
            paginator.append('```')

            await ctx.send('\n'.join(paginator))

    def cog_unload(self):
        self.task.cancel()


def setup(client):
    client.add_cog(AdventOfCode(client))
