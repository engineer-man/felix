"""This is a cog for a discord.py bot.
It adds a command to "remote control" the bot from the channel it is called in
The channel specified after the command will be the channel the bot posts
messages to and relays messages from.

Only the Person who started the remote control can use it and also stop it

Commands:
    rc          start remote control
    rc off      stop remote control
"""

from discord.ext import commands
from discord import TextChannel


class RemoteControl(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client
        self.rc_channel = None
        self.rc_user = None
        self.rc_target_channel = None
        self.rc_active = False

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    # ----------------------------------------------
    # Cog Event listeners
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, msg):
        if not self.rc_active:
            return
        if msg.author.bot:
            return
        if msg.channel == self.rc_target_channel:
            await self.rc_channel.send(msg.author.name + ':  ' + msg.content)
        elif msg.channel == self.rc_channel:
            if not msg.author == self.rc_user:
                return
            if msg.content.startswith('felix'):
                return
            await self.rc_target_channel.send(msg.content)
        else:
            return

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if not self.rc_active:
            return
        if not channel == self.rc_channel:
            return
        if not user == self.rc_user:
            return
        await self.rc_target_channel.trigger_typing()

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.group(
        invoke_without_command=True,
        name='rc',
        hidden=True,
    )
    async def remote_control(self, ctx, target_channel: TextChannel = None):
        """Remote control felix in a channel"""
        if self.rc_active:
            if not ctx.author == self.rc_user:
                await ctx.send(f'{self.rc_user.name} is currently using rc!')
                return
        if not target_channel:
            await ctx.send('Error: Please specify a channel!')
            return
        self.rc_target_channel = target_channel
        self.rc_user = ctx.author
        self.rc_channel = ctx.channel
        self.rc_active = True
        await ctx.send(f'Now remote controlling {target_channel.mention}')

    @remote_control.command(
        name='off',
    )
    async def rc_off(self, ctx):
        """Stop the remote control"""
        if not self.rc_active:
            return
        if not ctx.author == self.rc_user:
            await ctx.send(f'{self.rc_user.name} is currently using rc!')
            return
        self.rc_target_channel = None
        self.rc_user = None
        self.rc_channel = None
        self.rc_active = False
        await ctx.send(f'Remote Control Stopped!')


async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(RemoteControl(client))
