"""This is a cog for a discord.py bot.
It adds commands to print graphs of user message stats

Commands:
    graph       print help message
    ├ users     print graph containing specific users
    └ top       print graph containing most active users

This cog requires matplotlib:
    pip install -U matplotlib

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""
from discord.ext import commands
from discord import Member, File
from datetime import datetime, timedelta
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

    async def create_graph_messages(self, days, limit=0, users=None):
        url = 'https://emkc.org/api/v1/stats/discord/messages'
        if not users:
            # gets the top people of days and puts them in user_names
            params = {
                'start': (datetime.utcnow() - timedelta(days=days)).isoformat(),
                'limit': limit
            }
            async with self.client.session.get(url, params=params) as response:
                api_data = await response.json()
            if not api_data:
                return False
            user_names = [data['user'] for data in api_data]
            num_messages = {data['user']: data['messages']
                            for data in api_data}
        else:
            # puts specific people in user_names
            user_names = [str(user) for user in users]
            params = [
                ('start', (datetime.utcnow() - timedelta(days=days)).isoformat())]
            params += [('user', username) for username in user_names]
            async with self.client.session.get(url, params=params) as response:
                api_data = await response.json()
            if not api_data:
                return False
            num_messages = {data['user']: data['messages']
                            for data in api_data}

        graph_data = {name: [] for name in user_names}
        for i in range(days):
            startdate = datetime.utcnow() - timedelta(days=days - i)
            enddate = datetime.utcnow() - timedelta(days=days - i - 1)
            params = [('start', (startdate).isoformat()),
                      ('end', (enddate).isoformat())]
            params += [('user', username) for username in user_names]
            async with self.client.session.get(url, params=params) as response:
                api_data = await response.json()
            for data in api_data:
                if data['user'] in graph_data:
                    graph_data[data['user']].append([i, data['messages']])
        if all([not x for x in graph_data.values()]):
            return False
        for name, data in graph_data.items():
            xaxis = [i[0] for i in data]
            yaxis = [i[1] for i in data]
            templabel = '{} {}'.format(name[:-5], num_messages[name])
            plt.plot(xaxis, yaxis, label=templabel, marker='o', markersize=3)
        plt.legend()
        plt.ylabel('Messages')
        plt.xlabel(
            'Time since '
            f'{(datetime.utcnow() - timedelta(days=days)).isoformat()[:10]}'
            ' in days'
        )
        plt.savefig('last_graph.png', bbox_inches='tight')
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
        if days < 1:
            days = 1
        days += 1
        if n > 10:
            n = 10
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
        if days < 1:
            days = 1
        days += 1
        memberslist = [str(x) for x in members][:10]
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
