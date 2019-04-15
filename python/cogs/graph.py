"""This is a cog for a discord.py bot.
Graphing
"""

from discord.ext import commands
from discord import Member, File
from aiohttp import ClientSession
from datetime import datetime, timedelta
from os import path
import matplotlib.pyplot as plt
import asyncio
import json


class Graph(commands.Cog,
            name='Graph',
            command_attrs=dict(hidden=False)):
    def __init__(self, client):
        self.client = client
        self.session = ClientSession()
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            self.permitted_roles = json.load(f)[__name__.split('.')[-1]]

    async def cog_check(self, ctx):
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    async def create_graph_messages(self, n, limit=0, user=None):
        if not user:
            url = "https://emkc.org/api/v1/stats/discord/messages"

            """gets the top people of n days and puts them in toplist"""

            params = {
                'start': (datetime.now() - timedelta(days=n)).isoformat(),
                'limit': limit
            }
            async with self.session.get(url, params=params) as response:
                top = await response.json()
            toplist = []
            [toplist.append(i['user']) for i in top]
        else:

            """puts either the list of people or a signle person in toplist"""

            if type(user) == list:
                toplist = [i.replace('@', '') for i in user]
            else:
                toplist = [user.replace('@', '')]

        temp = {}
        for i in toplist:
            temp[i] = []
        for i in range(n):
            url = "https://emkc.org/api/v1/stats/discord/messages"
            date = datetime.now() - timedelta(days=n) + timedelta(days=i)
            date2 = datetime.now() - timedelta(days=n) + timedelta(days=i+1)
            params = {
                'start': (date).isoformat(),
                'end': (date2).isoformat(),
            }
            async with self.session.get(url, params=params) as response:
                messagesdaily = await response.json()
            tempday = {}
            [tempday.update({i['user']:i['messages']}) for i in messagesdaily]
            for i2 in tempday:
                for i3 in toplist:
                    if i3 in i2:
                        temp[i2].append([i+1, tempday[i3]])

        for x in temp:
            xaxis = [i[0] for i in temp[x]]
            yaxis = [i[1] for i in temp[x]]
            plt.plot(xaxis, yaxis, label=x)
        plt.legend()
        plt.ylabel("Messages")
        plt.xlabel("Time from start in days")
        plt.savefig("last_graph.png", bbox_inches='tight')
        plt.cla()
        print('success')

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.group(
        invoke_without_command=True,
        name='graph',
        brief='Print Graphs',
        description='Print Graphs',
        hidden=True,
    )
    @commands.guild_only()
    async def graph(self, ctx):
        await self.client.help_command.command_callback(ctx, command='graph')

    @graph.command(
        name='top',
        brief='Print Message Graphs',
        description='Print Message Graphs',
    )
    @commands.guild_only()
    async def top(
        self,
        ctx,
        days: int,
        top: int
    ):
        await self.create_graph_messages(days, top)
        with open('last_graph.png', 'rb') as g:
            file_to_send = File(g)
        await ctx.send(file=file_to_send)

    @graph.command(
        name='users',
        brief='Print Message Graphs',
        description='Print Message Graphs',
    )
    @commands.guild_only()
    async def users(
        self,
        ctx,
        days: int,
        members: commands.Greedy[Member]
    ):
        await self.create_graph_messages(days, 0, [str(x) for x in members])
        with open('last_graph.png', 'rb') as g:
            file_to_send = File(g)
        await ctx.send(file=file_to_send)

    def cog_unload(self):
        asyncio.ensure_future(self.session.close())


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Graph(client))
