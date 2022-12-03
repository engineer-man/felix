"""This is a cog for a discord.py bot.
It will announce if a user completed a puzzle on adventofcode.com

Commands:
    aoc         Print stats of specific day
    └ howto     Print help message

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('aoc')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('my_extensions.aoc')
"""
import asyncio
from datetime import datetime, timedelta
from unicodedata import normalize
from discord import Embed
from discord.ext import commands, tasks

# pylint: disable=E1101

API_URL = 'https://adventofcode.com/2022/leaderboard/private/view/208847.json'
AOC_CHANNEL = 778324114213175323
INTERVAL = 120

KNOWN_USERS = {
    '749969': 'JaminenB',
    '645784': 'Yamabushi',
    '676763': 'Tomzy',
    '995197': 'Ghostrunner0808',
    '959036': 'Bones',
    '996249': 'dev_null',
    '962475': 'dv_man',
    '419680': 'RuskyHacker',
    '1155906': 'T2',
    '2464982': 'hegehog',
    '2100497': 'Aetheridon',
    '2537005': 'mizatorian',
}


class AdventOfCode(commands.Cog, name='Advent of Code'):
    def __init__(self, client):
        self.client = client
        self.cookie = {'session': self.client.config['aoc_session']}
        self.members = {}
        self.aoc_task.start()
        self.last_msgs = []

    async def get_current_members(self):
        async with self.client.session.get(API_URL, cookies=self.cookie) as re:
            current_members = (await re.json())['members']
        for member_id, data in current_members.items():
            if member_id in KNOWN_USERS:
                data['name'] = KNOWN_USERS[member_id]
            if data['name'] is None:
                data['name'] = f'Anon_{member_id}'
            data['name'] = data['name'].replace('@', '')
            data['name'] = normalize(
                'NFKD', data['name']
            ).encode('ascii', 'ignore').decode('utf-8')
        return current_members

    @tasks.loop(seconds=INTERVAL)
    async def aoc_task(self):
        channel = self.client.main_guild.get_channel(AOC_CHANNEL)
        current_members = await self.get_current_members()
        msg = []
        for member_id, data in current_members.items():
            if member_id not in self.members:
                msg.append((
                    0,
                    f"#{data['name'].replace(' ','_')} " +
                    "has just joined the leaderboard."
                ))
                continue
            if data['stars'] == self.members[member_id]['stars']:
                continue
            new_stats = data['completion_day_level']
            old_stats = self.members[member_id]['completion_day_level']
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
                    time = int(new_stats[day][pzl]['get_star_ts'])
                    day1_time = int(new_stats[day]['1']['get_star_ts']) if pzl == '2' else 0
                    msg.append((
                        time,
                        f"#{data['name'].replace(' ', '_')} " +
                        f"solved [{day} - {pzl}] " +
                        f"at [{datetime.fromtimestamp(time).strftime('%H:%M:%S')} UTC] " +
                        (f"[Δ {timedelta(seconds=time - day1_time)}]" if pzl == '2' else "")
                    ))
        if msg:
            await channel.send(
                '\n'.join([
                    "```css",
                    '\n'.join([txt for _, txt in sorted(msg)]),
                    "```"
                ])
            )

        self.members = current_members

    @aoc_task.before_loop
    async def before_aoc_task(self):
        await self.client.wait_until_ready()
        self.members = await self.get_current_members()
        await asyncio.sleep(1)

    @commands.group(
        name='aoc',
        hidden=False,
        invoke_without_command=True,
    )
    async def aoc(self, ctx, day: int):
        """Show Advent of Code stats for a specific day
        (only works in #advent-of-code)"""
        if not 1 <= int(day) <= datetime.now().day:
            return
        day = str(day)
        if not ctx.channel.id == AOC_CHANNEL:
            return

        # Delete previous message
        for msg in self.last_msgs:
            await msg.delete()

        self.last_msgs = []

        members = await self.get_current_members()
        parts = {'1': {}, '2': {}}
        for data in members.values():
            days = data['completion_day_level']
            if day not in days:
                continue
            d = days[day]
            for k, v in d.items():
                parts[k][data['name']] = v['get_star_ts']
        if not parts['1'] and not parts['2']:
            await ctx.send(f'No data available for day {day}')
            return
        day1_times = {}
        for p in '12':
            paginator = []
            current = parts[p]
            if not current:
                continue
            paginator.append(f'Advent of Code puzzle [{day}]|[{p}]')
            first_time = 0
            for rank, entry in enumerate(sorted(current.items(), key=lambda x: x[1])):
                name, time = entry[0], int(entry[1])
                delta = ''
                if p == '1':
                    day1_times[name] = time
                else:
                    day1_time = day1_times.get(name, 0)
                    delta = f' [Δ {timedelta(seconds=time - day1_time)}]'

                if rank == 0:
                    first_time = time
                    paginator.append(
                        f'{rank+1}.{name.replace(" ","_")}'.ljust(27) +
                        f'[{datetime.fromtimestamp(first_time).strftime("%H:%M:%S")}]'
                        + delta
                    )
                else:
                    paginator.append(
                        f'{rank+1}.{name.replace(" ","_")}'.ljust(27) +
                        f'[+{timedelta(seconds=time - first_time)}]'
                        + delta
                    )

            if not paginator:
                return

            subs = [paginator[x:x+21] for x in range(0, len(paginator), 21)]
            for sub_paginator in subs:
                sub_paginator.insert(0, f'```css')
                sub_paginator.append('```')
                msg = await ctx.send('\n'.join(sub_paginator))
                self.last_msgs.append(msg)

    @aoc.command(
        name='howto',
        hidden=True,
        aliases=['how-to', 'help', 'faq'],
    )
    async def aoc_help(self, ctx):
        if not ctx.channel.id == AOC_CHANNEL:
            return
        text = """
        **Introduction**
        Advent of Code is a series of small programming puzzles for a variety of skill sets and skill levels in any programming language you like.
        It is held every year from the 1st to the 25th of December.
        Every day at `00:00 EST (05:00 UTC)` a new puzzle is released.
        When you log into the site you will be given a personalized puzzle input and every puzzle consists of 2 parts. The first part is usually a bit simpler - the second part often expands the problem so it can't simply be brute forced or guessed.

        I encourage you to read more about it on [the official homepage](https://adventofcode.com/2022/about).

        **This channel** will be used to discuss the puzzles.
        I recommend you only come here once you have solved the puzzle for the day or if you really need help to figure it out.

        **Leaderboards**
        There is a [global leaderboard](https://adventofcode.com/2022/leaderboard) which will reward the first person to solve a given puzzle part with 100 points. The second fastest will get 99 and so on.
        This global Leaderboard is usually very competitive and rather hard to get placed on.
        (Most of the time, all points for a puzzle will be gone after 5-30 minutes).
        This is why we have created a [private leaderboard](https://adventofcode.com/2022/leaderboard/private/view/208847).
        You can join it with the code `208847-c925c078`.
        **Users that did not collect at least 1 Star** last year have been removed from the leaderboard.

        **Important:** If you are new to programming, then the goal of this should not be to solve it as fast as possible.
        Don't be surprised if you get stuck on some challenges.
        I encourage you to try every puzzle without help for at least 30 minutes. When I started doing these puzzles, some took me multiple hours to solve.

        **If you want to prepare a bit** try to solve some [past challenges](https://adventofcode.com/2021/events).

        **Names** for the notifications sent in this channel are taken from adventofcode.com but can be customized.
        If your AOC name is different from your discord name, please contact an EM staff member."""

        embed = Embed(
            title='Advent of Code',
            description=text
        )
        embed.set_footer(
            text=ctx.author.display_name,
            icon_url=ctx.author.display_avatar
        )
        await ctx.send(embed=embed)

    def cog_unload(self):
        self.aoc_task.cancel()


async def setup(client):
    await client.add_cog(AdventOfCode(client))
