"""This is a cog for a discord.py bot.
it prints out either a random or specified chase pic,
the guide to those chase pics and some additional resources.

Commands:
    chase
    ├ num            print a specific chase pic
    └ random         prints a random chase pic
"""

import os
from random import choice
from discord.ext import commands, tasks
import re

class Chase(commands.Cog, name='Chase'):

    def __init__(self, client):
        self.url = "https://mydogchase.com"
        self.client = client
        self.pics_urls = []
        self.load_chase_pics.start()
        self.last_pic = None

    def cog_unload(self):
        self.load_chase_pics.cancel()

    @tasks.loop(hours=24)
    async def load_chase_pics(self):
        async with self.client.session.get(self.url) as res:
            text = await res.text()
            r = re.findall(r'/public/chase/.*\.jpg', text)
            self.pics_urls = sorted([f'{self.url}{pic}' for pic in r])

    def pick_random_chase_pic(self):
        c = choice(self.pics_urls)
        while c == self.last_pic:
            c = choice(self.pics_urls)
        self.last_pic = c
        return c

    def pick_exact_chase_pic(self, num):
        max_num = len(self.pics_urls)
        if num < 1 or num > max_num:
            raise commands.UserInputError(
                f"Input must be between `1` and `{max_num}` inclusive")
        return self.pics_urls[num - 1]

    async def get_chase_pic(self, ctx, n=0, random=False):
        await ctx.trigger_typing()
        try:
            if len(self.pics_urls) == 0:
                raise commands.CommandInvokeError(
                    f"No Chase pics available, please try again later")
            if random:
                await ctx.send(self.pick_random_chase_pic())
            else:
                await ctx.send(self.pick_exact_chase_pic(n))
        except Exception as e:
            await ctx.send(e)

    @commands.group(
        invoke_without_command=True,
        name='chase'
    )
    async def chase_pic(self, ctx, n: int):
        """'Show awesome Chase pics'"""
        await self.get_chase_pic(ctx, n=n)

    @chase_pic.command(
        name='r'
    )
    async def random_chase_pic(self, ctx):
        """Randomly choose a chase pic"""
        await self.get_chase_pic(ctx, random=True)

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Chase(client))

