"""This is a cog for a discord.py bot.
It will auto delete messages that contain certain links.
Discord invite link offenders will be informed 1 time every 10 minutes.
patreon and gofundme links are silently deleted

Commands:
    allow           Specify a user. User is then allowed to post 1
                    discord.gg invite link

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from discord import Member, DMChannel, Embed, Message, Member, TextChannel
from dataclasses import dataclass
import re
import time
import random

FORBIDDEN = [
    'patreon.com',
    'gofundme.com',
    'gofund.me'
]

REPORT_CHANNEL = 483978527549554698
REPORT_ROLE = 500710389131247636


class MyMember():
    # TODO: Make this a dataclass as soon as Felix run on py 3.7+
    def __init__(self, content, author, channel):
        self.content = content
        self.author = author
        self.channel = channel


class LinkBlocker(commands.Cog, name='Link Blocker'):
    def __init__(self, client):
        self.client = client
        self.allowed_once = []
        self.naughty_list = {}
        self.NAUGHTY_LIST_TIME = 600

    async def cog_check(self, ctx):
        return self.client.user_has_permission(ctx.author, 'linkblocker')

    # ----------------------------------------------
    # Message checks
    # ----------------------------------------------
    def is_dm(self, msg):
        """return True if message is a DM"""
        return isinstance(msg.channel, DMChannel)

    def is_allowed(self, msg):
        """return True if user is permitted to post links"""
        if msg.author == self.client.user:
            return True
        if self.client.user_has_permission(msg.author, 'linkblocker'):
            return True
        return False

    async def has_discord_link(self, msg):
        """Check message and return True if a discord link was detected"""
        if len(re.findall(r'(?i)(discord\.(gg|io|me)\/\S+)', msg.content)):
            if msg.author.id in self.allowed_once:
                self.allowed_once.remove(msg.author.id)
                return False
            else:
                if str(msg.author.id) in self.naughty_list:
                    last_time = self.naughty_list[str(msg.author.id)]
                    if time.time() - last_time > self.NAUGHTY_LIST_TIME:
                        self.naughty_list.pop(str(msg.author.id))
                    else:
                        return True
                await msg.channel.send(
                    f'Sorry {msg.author.mention}. ' +
                    'Posting links to other servers is not allowed.\n' +
                    'You can ask permission from an engineer-man team member!'
                )
                self.naughty_list[str(msg.author.id)] = time.time()
            return True
        return False

    async def has_forbidden_text(self, msg):
        """Check message and return True if forbidden text was detected"""
        if len(re.findall(
            r'(?i)(http(s)?\:\/\/(www\.)?(' +
            '|'.join([s.replace('.', '\\.') for s in FORBIDDEN]) +
            '))',
            msg.content
        )):
            return True
        return False

    async def post_report(self, msg):
        """Post report of deletion to target channel"""
        target = self.client.get_channel(REPORT_CHANNEL)
        e = Embed(description=msg.content,
                  color=random.randint(0, 0xFFFFFF))
        await target.send(
            f'<@&{REPORT_ROLE}> I deleted a message\n'
            f'Message sent by {msg.author.mention} in {msg.channel.mention}',
            embed=e
        )
        return True

    async def check_message(self, msg):
        """Check message - return True if message contains forbidden text"""
        my_msg = MyMember(msg.content, msg.author, msg.channel)
        # ignore spoiler tags
        my_msg.content = my_msg.content.replace('||', '')
        if self.is_dm(my_msg):
            return False
        if self.is_allowed(my_msg):
            return False
        if await self.has_discord_link(my_msg):
            return True
        if await self.has_forbidden_text(my_msg):
            return True
        return False

    # ----------------------------------------------
    # Event listeners
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, msg):
        if await self.check_message(msg):
            await msg.delete()
            await self.post_report(msg)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if await self.check_message(after):
            await after.delete()
            await self.post_report(after)

    # ----------------------------------------------
    # Command to allow 1 discord.gg link
    # ----------------------------------------------
    @commands.command(
        name='allow',
        hidden=True,
    )
    @commands.guild_only()
    async def allow(self, ctx, member: Member):
        """Allow a single discord.gg link by @user"""
        await ctx.send(f'Hey {member.mention}, you can post 1 discord.gg link!')
        self.allowed_once.append(member.id)


def setup(client):
    client.add_cog(LinkBlocker(client))
