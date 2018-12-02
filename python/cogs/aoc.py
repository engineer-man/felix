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
import json
import asyncio
import requests

with open("../config.json", "r") as conffile:
    config = json.load(conffile)

API_URL = 'https://adventofcode.com/2018/leaderboard/private/view/208847.json'
AOC_CHANNEL = 514527842399420427
EM_SERVER = 473161189120147456
INTERVAL = 180
cookie = {'session':config['aoc_session']}

class AdventOfCode():
    def __init__(self, client):
        self.client = client
        self.task = self.client.loop.create_task(self.aoc_monitor())
        self.members = {}

    async def on_ready(self):
        pass

    async def aoc_monitor(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        channel = self.client.get_guild(EM_SERVER).get_channel(AOC_CHANNEL)
        r = requests.get(API_URL, cookies=cookie)
        self.members = r.json()['members']
        try:
            while not self.client.is_closed():
                msg = []
                r = requests.get(API_URL, cookies=cookie)
                current_members = r.json()['members']
                for member, data in current_members.items():
                    if data['stars'] == self.members[member]['stars']:
                        continue
                    new_stats = data['completion_day_level']
                    old_stats = self.members[member]['completion_day_level']
                    current_stats = set()
                    for k,v in new_stats.items():
                        for s in v.keys():
                            current_stats.add(f'{k}-{s}')
                    previous_stats = set()
                    for k,v in old_stats.items():
                        for s in v.keys():
                            previous_stats.add(f'{k}-{s}')
                    for puzzle in sorted(current_stats):
                        if puzzle not in previous_stats:
                            day, pzl = puzzle.split('-')
                            msg.append(
                                f"#{data['name'].replace(' ', '_')} " +
                                f"solved: [Day {day}] - [Puzzle {pzl}]"
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


    def __unload(self):
        self.task.cancel()


def setup(client):
    client.add_cog(AdventOfCode(client))
