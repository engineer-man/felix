"""This is a cog for a discord.py bot.
It adds Yarr
"""
import random
from datetime import datetime as dt
from discord.ext import commands
from discord import Activity


class Yarr(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client
        self.last_yarr = dt.utcnow()
        self.chance = 4
        self.cooldown = 30
        random.seed()

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if random.randint(1, 100 // self.chance) == 1:
            if (dt.utcnow() - self.last_yarr).total_seconds() < self.cooldown:
                return
            yarr = self.get_yarr() + '!'
            await msg.channel.send(yarr)
            await self.client.change_presence(
                activity=Activity(name=yarr, type=0)
            )
            self.last_yarr = dt.utcnow()

    def get_yarr(self):
        yarrs = [
            'Ahoy',
            'Avast ye',
            'Batten down the hatches',
            'Blimey',
            'Give no quarter',
            'Heave ho',
            'Landlubber',
            'Shiver me timbers',
            'Walk the plank',
            'Yo ho ho',
            'YARR',
            'Aarrr',
            'Weigh anchor and hoist the mizzen',
            'Ahoy, me hearties',
            'Cleave him to the brisket',
            'Scurvy dog',
            'Three sheets to the wind',
        ]
        return random.choice(yarrs)


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Yarr(client))
