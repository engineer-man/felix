"""This is a cog for a discord.py bot.
It adds the purge command to the bot that can be used to delete messages

Commands:
    purge           Specify either an number of messages x or a list of users
                    or both
                    - If you specify a number the last x messages in the current
                      channel will be deleted
                    - If you specify a list of users all messages of these
                      users within the last 100 messages will be deleted
                    - If you specify both, all messages of the specified users
                      that are within the last x messages will be deleted.
    purge all       All messages in the channel will be deleted.
                    (might take a long time)

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from discord import Member
from inspect import Parameter
import typing
import asyncio


class Purge(commands.Cog, name='Purge'):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return self.client.user_has_permission(ctx.author, 'purge')

    # ----------------------------------------------
    # Function Group to clear channel of messages
    # ----------------------------------------------
    @commands.group(
        invoke_without_command=True,
        name='purge',
        brief='Clear messages from current channel',
        description='Clear messages from current channel'
        + '\nExamples:'
        + '\n*  purge 10'
        + '\n*  purge @user'
        + '\n*  purge 10 @user  -  (number of messages first, then user)'
        + '\n*  purge @user 10  -  (user first, then number of messages)'
        + '\n*  purge @user1 @user2'
        + '\n*  purge all       -  (delete all messages in current channel)',
        hidden=True,
    )
    @commands.guild_only()
    async def purge(
        self, ctx,
        n: typing.Optional[int] = 0,
        users: commands.Greedy[Member] = [],
        n2: typing.Optional[int] = 0,
        # This allows the command to be used with either order of [num] [user]
    ):
        if not users and not n:
            param = Parameter('number_of_messages', Parameter.POSITIONAL_ONLY)
            raise commands.MissingRequiredArgument(param)
        channel = ctx.message.channel
        if not users:
            msg_limit = n+1 if n else 100
            await channel.purge(limit=msg_limit, check=None, before=None)
        else:
            if n2:
                n = n2

            userids = [user.id for user in users]

            def check(m):
                return any(m.author.id == userid for userid in userids)

            msg_limit = n if n else 100
            await ctx.message.delete()
            await channel.purge(limit=msg_limit, check=check, before=None)
        return True

    @purge.command(
        name='all',
        brief='Clear all messages in current channel',
        description='Clear all messages in current channel\n' +
        'A security question will be asked before proceeding')
    @commands.guild_only()
    async def purge_all(self, ctx):
        channel = ctx.message.channel
        caller = ctx.author

        def check(m):
            return m.author.id == caller.id and m.channel.id == channel.id

        confirmation_q = await channel.send(
            'Are you sure you want to delete all messages in this channel?' +
            '\nThis might take a very long time.' +
            '\nIf you are sure please enter the channel name.'
        )
        try:
            confirmation_a = await self.client.wait_for('message',
                                                        check=check,
                                                        timeout=30)
        except asyncio.TimeoutError:
            await channel.send(f'TIMEOUT - waited more than 30 sec')
            return
        if confirmation_a.content == channel.name:
            await channel.purge(limit=100000, check=None, before=None)
        else:
            await ctx.message.delete()
            await confirmation_q.delete()
            await confirmation_a.delete()
        return True


def setup(client):
    client.add_cog(Purge(client))
