"""This is a cog for a discord.py bot.
it prints out either a random or specified chase pic,
the guide to those chase pics and some additional resources.

Commands:
    chase
    ├ num            print a specific chase pic
    └ random         prints a random chase pic
"""

import re
from random import choice
from discord.ext import commands, tasks

#pylint: disable=E1101


class Chase(commands.Cog, name='Chase'):

    def __init__(self, client):
        self.client = client
        self.load_chase_pics.start()
        self.all_pictures = {}
        self.unseen_pictures = []

    @tasks.loop(hours=24)
    async def load_chase_pics(self):
        url = "https://mydogchase.com"
        async with self.client.session.get(url) as res:
            text = await res.text()
            r = re.findall(r'/public/chase/.*\.jpg', text)
            self.all_pictures = {i: f'{url}{pic}' for i, pic in enumerate(sorted(r))}

    def cog_unload(self):
        self.load_chase_pics.cancel()

    async def post_chase_pic(self, ctx, num=0, random=False):
        #await ctx.trigger_typing()
        if len(self.all_pictures) == 0:
            raise commands.BadArgument(f"No Chase pics available")
        if random:
            if not self.unseen_pictures:
                self.unseen_pictures = list(range(len(self.all_pictures)))
            num = choice(self.unseen_pictures)
            self.unseen_pictures.remove(num)
        else:
            if not 0 <= num < len(self.all_pictures):
                raise commands.BadArgument(f"Choose number from `0-{len(self.all_pictures)-1}`")
        await ctx.send(f'Picture #{num}: {self.all_pictures[num]}')

    @commands.group(
        invoke_without_command=True,
        name='chase',
    )
    async def chase_pic(self, ctx, num: int):
        """'Show a specific chase pic'"""
        await self.post_chase_pic(ctx, num=num)

    @chase_pic.command(
        name='random',
        aliases=['r'],
    )
    async def random_chase_pic(self, ctx):
        """Randomly choose a chase pic"""
        await self.post_chase_pic(ctx, random=True)


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Chase(client))
