"""This is a cog for a discord.py bot.
It will auto delete messages that contain certain links.
Discord invite link offenders will be informed 1 time every 10 minutes.
patreon and gofundme links are silently deleted

Commands:
    allow           Specify a user. User is then allowed to post 1
                    discord.gg invite link

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('linkblocker')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('cogs.linkblocker')

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from discord import Member, DMChannel
from os import path
import json
import re
import time

FORBIDDEN = [
    'patreon.com',
    'gofundme.com',
    'gofund.me'
]


class LinkBlocker():
    def __init__(self, client):
        self.client = client
        self.allowed = []
        self.naughty_list = {}
        self.naughty_list_time = 600
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            self.permitted_roles = json.load(f)[__name__.split('.')[-1]]

    async def __local_check(self, ctx):
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    # ----------------------------------------------
    # Message checks
    # ----------------------------------------------
    def check_dm(self, msg):
        """return True if message is a DM"""
        if isinstance(msg.channel, DMChannel):
            # Dont check Direct Messages
            return True
        return False

    def check_permissions(self, msg):
        """return True if user is permitted to post links"""
        author_roles = [role.id for role in msg.author.roles]
        if not self.client.user == msg.author:
            if any(role in self.permitted_roles for role in author_roles):
                # Don't check messages by users with allowed roles
                return True
        return False

    async def check_discord(self, msg):
        """Do stuff and return True if discord link was detected"""
        if isinstance(msg.channel, DMChannel):
            # Dont check Direct Messages
            return False
        author_roles = [role.id for role in msg.author.roles]
        if not self.client.user == msg.author:
            if any(role in self.permitted_roles for role in author_roles):
                # Don't check messages by users with allowed roles
                return False
        if len(re.findall(r'(?i)(discord\.(gg|io|me)\/\S+)', msg.content)):
            if self.client.user == msg.author:
                await msg.delete()
            elif msg.author.id in self.allowed:
                self.allowed.remove(msg.author.id)
            else:
                await msg.delete()
                if str(msg.author.id) in self.naughty_list:
                    last_time = self.naughty_list[str(msg.author.id)]
                    if time.time() - last_time > self.naughty_list_time:
                        self.naughty_list.pop(str(msg.author.id))
                    else:
                        return
                await msg.channel.send(
                    f'Sorry {msg.author.mention}. ' +
                    'Posting Links to other servers is not allowed.\n' +
                    'You can ask permission from an engineer-man team member!'
                )
                self.naughty_list[str(msg.author.id)] = time.time()
            return True
        return False

    async def check_forbidden(self, msg):
        """Delete message and return True if forbidden link was detected"""
        if len(re.findall(
            r'(?i)(http(s)?\:\/\/(www\.)?(' +
            '|'.join([s.replace('.', '\\.') for s in FORBIDDEN]) +
            '))',
            msg.content
        )):
            await msg.delete()
            return True
        return False

    # ----------------------------------------------
    # Event listeners
    # ----------------------------------------------
    async def check_message(self, msg):
        """Run all checks on a message"""
        if self.check_dm(msg):
            return
        if self.check_permissions(msg):
            return
        if await self.check_discord(msg):
            return
        if await self.check_forbidden(msg):
            return

    async def on_message(self, msg):
        await self.check_message(msg)

    async def on_message_edit(self, before, after):
        await self.check_message(after)

    # ----------------------------------------------
    # Method to allow 1 discord.gg link
    # ----------------------------------------------
    @commands.command(
        name='allow',
        brief='Allow a single discord.gg link.',
        description='Allow a single discord.gg link.',
        hidden=True,
    )
    @commands.guild_only()
    async def allow(self, ctx, member: Member):
        await ctx.send(f'Hey {member.mention}, you can post 1 discord.gg link!')
        self.allowed.append(member.id)


def setup(client):
    client.add_cog(LinkBlocker(client))
