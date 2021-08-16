"""This is a cog for a discord.py bot.
It adds the purge command to the bot that can be used to delete messages

Commands:
    purge <n>               Delete the last n messages
    purge_user <User> [n]   Delete all messages of <User> within the last
                            [n] Messages (Default 100)

Only users that have an admin role can use the commands.
"""
import typing
from datetime import timedelta
from discord.ext import commands
from discord import User, errors, TextChannel, Forbidden


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
        num_messages: int,
    ):
        """Clear <n> messages from current channel"""
        channel = ctx.message.channel
        await ctx.message.delete()
        await channel.purge(limit=num_messages, check=None, before=None)
        return True

    @commands.command(
        name='purge_until',
        hidden=True,
    )
    async def purge_until(
        self, ctx,
        message_id: int,
    ):
        """Clear messages in a channel until the given message_id. Given ID is not deleted"""
        channel = ctx.message.channel
        try:
            message = await channel.fetch_message(message_id)
        except errors.NotFound:
            await ctx.send("Message could not be found in this channel")
            return

        await ctx.message.delete()
        await channel.purge(after=message)
        return True

    @commands.command(
        name='purge_user',
        hidden=True,
        aliases=['purgeu', 'purgeuser'],
    )
    async def purge_user(
        self, ctx,
        user: User,
        num_messages: typing.Optional[int] = 100,
    ):
        """Clear all messagges of <User> withing the last [n=100] messages"""
        channel = ctx.message.channel

        def check(msg):
            return msg.author.id == user.id

        await ctx.message.delete()
        await channel.purge(limit=num_messages, check=check, before=None)

    @commands.command(
        name='purge_user_time',
        hidden=True,
        aliases=['purgeut', 'purgeusertime'],
    )
    async def purge_user_time(
        self, ctx,
        user: User,
        num_minutes: typing.Optional[int] = 5,
    ):
        """Clear all messages of <User> in every channel withing the last [n=5] minutes"""
        after = ctx.message.created_at - timedelta(minutes=num_minutes)

        def check(msg):
            return msg.author.id == user.id

        await ctx.message.delete()
        for channel in await ctx.guild.fetch_channels():
            if type(channel) is TextChannel:
                try:
                    await channel.purge(limit=10*num_minutes, check=check, after=after)
                except Forbidden:
                    continue


def setup(client):
    client.add_cog(Purge(client))
