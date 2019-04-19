"""This is a cog for a discord.py bot.
It will add a poll command for everyone to use

Commands:
    poll            Create a poll

Each user only has 1 vote and the bot will remove previous votes if a user
votes a second time.
The bot will also remove any new reactions added to the message.

NOTE that the bot can only check reactions on the last 15000 messages it saw.
So after 15000 messages (max_messages setting) the poll monitoring breaks.
It also breaks if the poll-cog is reloaded or the bot is restarted.

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

from discord.ext import commands
from os import path
import re


class Poll(commands.Cog, name='Poll'):
    def __init__(self, client):
        self.client = client
        self.polls = {}
        self.emoji = {
            "0": "0\u20e3",
            "1": "1\u20e3",
            "2": "2\u20e3",
            "3": "3\u20e3",
            "4": "4\u20e3",
            "5": "5\u20e3",
            "6": "6\u20e3",
            "7": "7\u20e3",
            "8": "8\u20e3",
            "9": "9\u20e3",
            "a": "🇦",
            "b": "🇧",
            "c": "🇨",
            "d": "🇩",
            "e": "🇪",
            "f": "🇫",
            "g": "🇬",
            "h": "🇭",
            "i": "🇮",
            "j": "🇯",
            "k": "🇰",
            "l": "🇱",
            "m": "🇲",
            "n": "🇳",
            "o": "🇴",
            "p": "🇵",
            "q": "🇶",
            "r": "🇷",
            "s": "🇸",
            "t": "🇹",
            "u": "🇺",
            "v": "🇻",
            "w": "🇼",
            "x": "🇽",
            "y": "🇾",
            "z": "🇿"
        }
        self.permitted_roles = self.client.permissions(path.dirname(__file__))['poll']

    async def cog_check(self, ctx):
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        msg = reaction.message
        message_id = str(msg.id)
        if user.bot:
            return
        if message_id in self.polls:
            if reaction.emoji not in self.polls[message_id]:
                await msg.remove_reaction(reaction, user)
            else:
                for r in msg.reactions:
                    async for u in r.users():
                        if not u.id == user.id:
                            continue
                        if r.emoji == reaction.emoji:
                            continue
                        await msg.remove_reaction(r, user)

    # ----------------------------------------------
    # Function to make a poll
    # ----------------------------------------------

    @commands.command(
        name='poll',
        brief='Create a Poll',
        description='Example use:' +
        '\npoll\nQuestion' +
        '\n0. Possibility0' +
        '\n1: Possibility1' +
        '\na. Possibility2' +
        '\nb) Possibility3',
        hidden=True,
    )
    async def make_poll(self, ctx, *, poll_string):
        re_find = re.findall(
            r'^([0-9a-zA-Z])(?:\.|\:|\))\s', poll_string, flags=re.M
        )
        choices = [r for r in re_find]
        poll_msg = ctx.message
        poll_id = str(poll_msg.id)
        for choice in choices:
            react_emoji = self.emoji[choice.lower()]
            self.polls[poll_id] = self.polls.get(poll_id, []) + [react_emoji]
            await poll_msg.add_reaction(react_emoji)


def setup(client):
    client.add_cog(Poll(client))
