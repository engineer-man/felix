import random
import re
import typing
from datetime import datetime as dt
from urllib.parse import quote
from discord.ext import commands
from discord import Embed, DMChannel, Member

class Fun(commands.Cog, name='Fun'):
    def __init__(self, client):
        self.client = client

    # ----------------------------------------------
    # Helper Functions
    # ----------------------------------------------
    def get_uwu_string(self, string):
        ret=string.replace(';)', 'UwU').replace(':)', 'OwO').replace('u', 'uw').replace('youw', 'u').replace('l', 'w').replace('r', 'w').replace('ga', 'gwa').replace('thewe', 'thwere')
        return ret

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------

    @commands.command(name='uwuify')
    async def uwuify(self, ctx, *, string):
        await ctx.trigger_typing()
        e = Embed(
            color=0x00ff00,
            title='UwUified!',
            description=f"`{self.get_uwu_string(string)}`. Hope you're happy.",
        )

        await ctx.send(embed=e)

def setup(client):
    client.add_cog(UwUify(client))
