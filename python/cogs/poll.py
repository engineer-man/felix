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

Only users that have an admin role can use the commands.
"""

import re
from discord.ext import commands


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

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

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
        hidden=True,
    )
    async def make_poll(self, ctx, *, poll_string):
        """Create a Poll
        Example use:
        ```
        felix poll
        Question
        0. Possibility0
        1: Possibility1
        a. Possibility2
        b) Possibility3
        ```"""
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


async def setup(client):
    await client.add_cog(Poll(client))
