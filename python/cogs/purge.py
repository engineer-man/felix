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

Only users that have an admin role can use the commands.
"""

import typing
from inspect import Parameter
from discord.ext import commands
from discord import Member, User


class Purge(commands.Cog, name='Purge'):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    # ----------------------------------------------
    # Function Group to clear channel of messages
    # ----------------------------------------------
    @commands.command(
        name='purge',
        hidden=True,
    )
    async def purge(
        self, ctx,
        n: typing.Optional[int] = 0,
        users: commands.Greedy[typing.Union[Member, User]] = [],
        n2: typing.Optional[int] = 0
        # This allows the command to be used with either order of [num] [user]
    ):
        """Clear messages from current channel
        ```
        Examples:
        *  purge 10
        *  purge @user
        *  purge 10 @user
        *  purge @user 10
        *  purge @user1 @user2
        ```"""
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


def setup(client):
    client.add_cog(Purge(client))
