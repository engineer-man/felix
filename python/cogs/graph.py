"""This is a cog for a discord.py bot.
Graphing
"""
from discord.ext import commands
from discord import Member, File
from datetime import datetime, timedelta
from multidict import CIMultiDict
import matplotlib.pyplot as plt


class Graph(commands.Cog,
            name='Graph',
            command_attrs=dict(hidden=False)):
    def __init__(self, client):
        self.client = client
        self.permitted_roles = self.client.permissions['graph']

    async def cog_check(self, ctx):
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    async def create_graph_messages(self, n, limit=0, user=None):
        url = "https://emkc.org/api/v1/stats/discord/messages"
        if not user:

            """gets the top people of n days and puts them in toplist"""

            params = {
                'start': (datetime.now() - timedelta(days=n)).isoformat(),
                'limit': limit
            }
            async with self.client.session.get(url, params=params) as response:
                top = await response.json()
            toplist = []
            totalmsg = {}
            [totalmsg.update({i['user']: i['messages']}) for i in top]
            [toplist.append(i['user']) for i in top]
            if not top:
                return False
        else:

            """puts either the list of people or a signle person in toplist"""

            if type(user) == list:
                toplist = [i.replace('@', '') for i in user]
            else:
                toplist = [user.replace('@', '')]
            params = [
                ('start', (datetime.now() - timedelta(days=n)).isoformat())]
            params += [("user", i) for i in toplist]
            async with self.client.session.get(url, params=params) as response:
                top = await response.json()
            if not top:
                return False
            totalmsg = {}
            [totalmsg.update({i['user']: i['messages']}) for i in top]
        temp = {}
        for i in toplist:
            temp[i] = []
        for i in range(n):
            date = datetime.now() - timedelta(days=n) + timedelta(days=i)
            date2 = datetime.now() - timedelta(days=n) + timedelta(days=i+1)
            params = [('start', (date).isoformat()),
                      ('end', (date2).isoformat())]
            params += [("user", i) for i in toplist]
            async with self.client.session.get(url, params=params) as response:
                messagesdaily = await response.json()
            for x in messagesdaily:
                if x['user'] in temp:
                    temp[x['user']].append([i+1, x['messages']])
        if all([not x for x in temp.values()]):
            return False
        for x in temp:
            xaxis = [i[0] for i in temp[x]]
            yaxis = [i[1] for i in temp[x]]
            templabel = '{} {}'.format(x[:-5], totalmsg[x])
            plt.plot(xaxis, yaxis, label=templabel, marker='o', markersize=3)
        plt.legend()
        plt.ylabel("Messages")
        plt.xlabel(
            f"Time since {(datetime.now() - timedelta(days=n)).isoformat()[:10]} in days")
        plt.savefig("last_graph.png", bbox_inches='tight')
        plt.cla()
        return True

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
        brief='Print Message Graph',
        description=('Print Message Graph of the top n ' +
                     'users over the specified number of days'),
    )
    @commands.guild_only()
    async def top(
        self,
        ctx,
        n: int,
        days: int
    ):
        await ctx.trigger_typing()
        if days > 30:
            days = 30
        if n > 10:
            n = 10
            await ctx.send('Cut down to 10 people')
            await ctx.trigger_typing()
        if not days or not n:
            return
        if await self.create_graph_messages(days, n):
            with open('last_graph.png', 'rb') as g:
                file_to_send = File(g)
            await ctx.send(file=file_to_send)
        else:
            await ctx.send('Nothing found')

    @graph.command(
        name='users',
        brief='Print Message Graph',
        description=('Print Message Graph of the specified ' +
                     'users over the specified number of days'),
    )
    @commands.guild_only()
    async def users(
        self,
        ctx,
        members: commands.Greedy[Member],
        days: int
    ):
        await ctx.trigger_typing()
        if days > 30:
            days = 30
        memberslist = [str(x) for x in members]
        if len(memberslist) > 10:
            memberslist = memberslist[:10]
            await ctx.send('Cut down to 10 people')
            await ctx.trigger_typing()

        if not days or not memberslist:
            return
        if await self.create_graph_messages(days, 0, memberslist):
            with open('last_graph.png', 'rb') as g:
                file_to_send = File(g)
            await ctx.send(file=file_to_send)
        else:
            await ctx.send('Nothing found')


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Graph(client))
