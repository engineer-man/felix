"""This is a cog for a discord.py bot.
It will add a poll command for everyone to use

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('poll')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('my_extensions.poll')

"""

from discord.ext import commands
import re


class Poll():
    def __init__(self, client):
        self.client = client
        self.polls = {}
        self.e_numbers = [
            "0\u20e3",
            "1\u20e3",
            "2\u20e3",
            "3\u20e3",
            "4\u20e3",
            "5\u20e3",
            "6\u20e3",
            "7\u20e3",
            "8\u20e3",
            "9\u20e3",
        ]

    async def on_reaction_add(self, reaction, user):
        msg = reaction.message
        message_id = str(msg.id)
        if user.bot:
            return
        if message_id in self.polls:
            if len(msg.reactions) > self.polls[message_id]:
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
    @commands.command(name='poll',
                      brief='Create a Poll',
                      description='Example use:' +
                      '\n!poll Question' +
                      '\n0.Possibility0' +
                      '\n1.Possibility1' +
                      '\n7.Possibility7' +
                      '\n3.Possibility3',
                      )
    async def make_poll(self, ctx, *poll_tuple: str):
        poll = list(poll_tuple)
        if not poll:
            return
        choices_str = ''.join(poll)
        choices = [int(r) for r in re.findall(r'([0-9])\.', choices_str)]

        mymsg = ctx.message
        self.polls[str(mymsg.id)] = len(choices)
        for choice in choices:
            await mymsg.add_reaction(self.e_numbers[choice])



def setup(client):
    client.add_cog(Poll(client))
