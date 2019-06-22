"""This is a cog for a discord.py bot.
It adds commands to print graphs of user message stats

Commands:
    graph       print help message
    ├ users     print graph containing specific users
    └ top       print graph containing most active users

This cog requires matplotlib:
    pip install -U matplotlib

Only users that have an admin role can use the commands.
"""
from discord.ext import commands
from discord import Member, File
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def clamp(value: int, low: int, high: int):
    if value < low:
        return low
    if value > high:
        return high
    return value


class Graph(commands.Cog,
            name='Graph',
            command_attrs=dict(hidden=False)):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

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
            params = [(
                'start',
                (datetime.utcnow() - timedelta(days=days)).isoformat()
            )]
            params += [('user', username) for username in user_names]
            async with self.client.session.get(url, params=params) as response:
                api_data = await response.json()
            if not api_data:
                return False
            num_messages = {data['user']: data['messages']
                            for data in api_data}
            user_names = sorted(
                user_names,
                key=lambda x: num_messages[x],
                reverse=True
            )
        graph_data = {name: [[0, 0]] for name in user_names}
        for i in range(days):
            startdate = datetime.utcnow() - timedelta(days=days - i)
            enddate = datetime.utcnow() - timedelta(days=days - i - 1)
            params = [('start', (startdate).isoformat()),
                      ('end', (enddate).isoformat())]
            params += [('user', username) for username in user_names]
            async with self.client.session.get(url, params=params) as response:
                api_data = await response.json()
            retrieved_users = {x['user']: x for x in api_data}
            for username, data in graph_data.items():
                if data:
                    current_msg = data[-1][1]
                else:
                    current_msg = 0
                if username not in retrieved_users:
                    new_messages = current_msg
                else:
                    api_data = retrieved_users[username]
                    new_messages = current_msg + api_data['messages']
                data.append([i+1, new_messages])
        if all([not x for x in graph_data.values()]):
            return False
        for name, data in graph_data.items():
            xaxis = [i[0] for i in data]
            yaxis = [i[1] for i in data]
            templabel = '{} {}'.format(name[:-5], num_messages[name])
            plt.plot(xaxis, yaxis, label=templabel, marker='o', markersize=3)
        plt.legend()
        plt.ylabel('Messages')
        label_time = (datetime.utcnow() - timedelta(days=days)).isoformat()
        plt.xlabel(
            'Time in days since '
            f'{label_time.split(".")[0].replace("T", " ")}'
            ' UTC'
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
        hidden=True,
    )
    @commands.guild_only()
    async def graph(self, ctx):
        """Print Graphs"""
        await ctx.send_help('graph')

    @graph.command()
    @commands.guild_only()
    async def top(
        self,
        ctx,
        n: int,
        days: int
    ):
        """Print graph of top n users
        measured by the number of messages in the last [days] days
        """
        await ctx.trigger_typing()
        days = clamp(days, 1, 30)
        n = clamp(n, 1, 10)
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
        """Print graph of specific users
        measure over the last [days] days
        """
        if not members:
            raise commands.BadArgument('Please specify at least 1 member')
        await ctx.trigger_typing()
        days = clamp(days, 1, 30)
        memberslist = [str(x) for x in members][:10]
        if await self.create_graph_messages(days, 0, memberslist):
            with open('last_graph.png', 'rb') as g:
                file_to_send = File(g)
            await ctx.send(file=file_to_send)
        else:
            await ctx.send('Nothing found')


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Graph(client))
