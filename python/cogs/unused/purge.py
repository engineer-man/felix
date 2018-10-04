"""This is a cog for a discord.py bot.
It adds the purge command to the bot that can be used to delete messages

Commands:
    purge           Specify either an number of messages x or a list of users
                    or both
                    - If you specify a number the last x messages in the current
                      channel will be deleted
                    - If you specify a list of users all messages of these
                      users within the last 1000 messages will be deleted
                    - If you specify both, all messages of the specified users
                      that are withing the last x messages will be deleted.
    purge all       The last 1000 messages in the channel will be deleted.
                    (might take a long time)


Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('purge')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('cogs.purge')

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from discord import Member
from os import path
import json
import typing


class Purge():
    def __init__(self, client):
        self.client = client
        # Load id's of roles that are allowed to use commands from this cog
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            self.permitted_roles = json.load(f)[__name__.split('.')[-1]]

    async def __local_check(self, ctx):
        # if await ctx.bot.is_owner(ctx.author):
        #     return True
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    # ----------------------------------------------
    # Function Group to clear channel of messages
    # ----------------------------------------------
    @commands.group(
        invoke_without_command=True,
        name='purge',
        brief='Clear messages from current channel',
        description='Clear messages from current channel',
        hidden=True,
    )
    @commands.guild_only()
    async def purge(self, ctx,
                    n: typing.Optional[int] = 0,
                    users: commands.Greedy[Member] = [],
                    n2: typing.Optional[int] = 0,
                    ):
        if not users and not n:
            return
        channel = ctx.message.channel
        if not users:
            msg_limit = n+1 if n else 1000
            await channel.purge(limit=msg_limit, check=None, before=None)
        else:
            if n2:
                n = n2

            def check(m):
                userids = [user.id for user in users]
                return any(m.author.id == userid for userid in userids)
            msg_limit = n+1 if n else 1000
            await channel.purge(limit=msg_limit, check=check, before=None)
        return True

    @purge.command(name='all',
                   brief='Clear 1000 messages in current channel',
                   description='Clear 1000 messages in current channel')
    @commands.guild_only()
    async def purge_all(self, ctx):
        channel = ctx.message.channel
        await channel.purge(limit=1000, check=None, before=None)
        return True


def setup(client):
    client.add_cog(Purge(client))
