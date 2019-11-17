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
from discord import Embed
from discord.ext import commands, tasks

# pylint: disable=E1101

API_URL = 'https://adventofcode.com/2019/leaderboard/private/view/208847.json'
AOC_CHANNEL = 647509035465048084
INTERVAL = 120


class AdventOfCode(commands.Cog, name='Advent of Code'):
    def __init__(self, client):
        self.client = client
        self.cookie = {'session': self.client.config['aoc_session']}
        self.members = {}
        self.aoc_task.start()

    @tasks.loop(seconds=INTERVAL)
    async def aoc_task(self):
        channel = self.client.main_guild.get_channel(AOC_CHANNEL)
        async with self.client.session.get(API_URL, cookies=self.cookie) as re:
            current_members = (await re.json())['members']
        msg = []
        for member_id, data in current_members.items():
            if member_id not in self.members:
                msg.append(
                    f"#{data['name'].replace(' ','_')} " +
                    "has just joined the leaderboard."
                )
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

    @aoc_task.before_loop
    async def before_aoc_task(self):
        await self.client.wait_until_ready()
        async with self.client.session.get(API_URL, cookies=self.cookie) as re:
            self.members = (await re.json())['members']
        await asyncio.sleep(INTERVAL)

    @commands.group(
        name='aoc',
        hidden=False,
        invoke_without_command=True,
    )
    async def aoc(self, ctx, day: int):
        """Show Advent of Code stats for a specific day
        (only works in #advent-of-code)"""
        if int(day) < 1 or int(day) > 24:
            return
        if not ctx.channel.id == AOC_CHANNEL:
            return
        async with self.client.session.get(API_URL, cookies=self.cookie) as re:
            members = (await re.json())['members']
        parts = {'1': [], '2': []}
        for data in members.values():
            days = data['completion_day_level']
            if day not in days:
                continue
            d = days[day]
            for k, v in d.items():
                parts[k].append((v['get_star_ts'], data['name']))
        if not parts['1'] or not parts['2']:
            await ctx.send(f'No data available for day {day}')
            return
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

    @aoc.command(
        name='howto',
        aliases=['how-to', 'help', 'faq'],
    )
    async def aoc_help(self, ctx):
        if not ctx.channel.id == AOC_CHANNEL:
            return
        text = """
        **Introduction**
        Advent of Code is a series of small programming puzzles for a variety of skill sets and skill levels in any programming language you like.
        It is held every year from the 1st to the 25th of December.
        Every day at `00:00 EST` a new puzzle is released.
        When you log into the site you will be given a personalized puzzle input and every puzzle consists of 2 parts. The first part is usually a bit simpler - the second part often expands the problem so it can't simply be brute forced or guessed.

        I encourage you to read more about it on [the official homepage](https://adventofcode.com/2019/about).

        **This channel** will be used to discuss the puzzles.
        I recommend you only come here once you have solved the puzzle for the day or if you really need help to figure it out.

        **Leaderboards**
        There is a [global leaderboard](https://adventofcode.com/2019/leaderboard) which will reward the first person to solve a given puzzle part with 100 points. The second fastest will get 99 and so on.
        This global Leaderboard is usually very competitive and rather hard to get placed on.
        (Most of the time, all points for a puzzle will be gone after 5-30 minutes).
        This is why i have created a [private leaderboard](https://adventofcode.com/2019/leaderboard/private/view/208847).
        You can join it with the code `208847-9f5fc5f3` and it will track the amount of stars everyone has.

        **Important:** The goal of this should not be to solve it as fast as possible.
        If you are new to programming, you might get stuck on some challenges.
        I encourage you to try every puzzle without help for at least 30 minutes. When I started doing these puzzles, some took me multiple hours to solve.

        **If you want to prepare a bit** try to solve some [past challenges](https://adventofcode.com/2018/events)."""

        embed = Embed(
            title='Advent of Code',
            description=text
        )
        embed.set_footer(
            text=ctx.author.display_name,
            icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)

    def cog_unload(self):
        self.aoc_task.cancel()


def setup(client):
    client.add_cog(AdventOfCode(client))
