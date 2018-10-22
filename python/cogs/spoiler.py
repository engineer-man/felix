"""This is a cog for a discord.py bot.
It enables users to create spoiler messages using the bot
Commands:
    spoiler         Start the spoiler setup process

Load the cog by calling client.load_extension with the name of this python file
as an argument (without .py)
    example:    bot.load_extension('example')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('folder.example')
"""

from discord.ext import commands
from discord import DMChannel, Embed, Color
import asyncio


class Spoiler():
    def __init__(self, client):
        self.client = client
        self.spoilers = {}
        self.qm = '❓'
        self.timeout = 60

    def get_spoiler_embed(self, title, user, text=None):
        description = text or f'React with {self.qm} to reveal the spoiler.'
        embed = Embed(
            title=title,
            description=description,
            color=Color.dark_gold())
        embed.set_author(name=user, icon_url=user.avatar_url_as(format='png'))
        return embed

    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        id_str = str(reaction.message.id)
        if id_str not in self.spoilers:
            return
        if reaction.emoji == self.qm:
            title, text, spoiler_author = self.spoilers[id_str]
            embed = self.get_spoiler_embed(title, spoiler_author, text)
            await user.send(embed=embed)

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.command(
        name='spoiler',
        brief='Create a Spoiler message',
        description='Use Felix to create a spoiler message',
        hidden=False,
    )
    @commands.guild_only()
    async def make_spoiler(self, ctx):
        user = ctx.message.author

        def check(m):
            return m.author.id == user.id and isinstance(m.channel, DMChannel)

        await ctx.message.delete()
        try:
            await user.send(
                f'Hi {user.name}, please tell me the title of your spoiler.'
            )
            msg_title = await self.client.wait_for('message',
                                                   check=check,
                                                   timeout=self.timeout)
            title = msg_title.content
            await user.send('Okay, now tell me the text of your spoiler.')
            msg_text = await self.client.wait_for('message',
                                                  check=check,
                                                  timeout=self.timeout)
            text = msg_text.content
        except asyncio.TimeoutError:
            await user.send(f'TIMEOUT - waited more than {self.timeout} sec')
            return

        embed = self.get_spoiler_embed(title, user)
        spoiler_msg = await ctx.message.channel.send(embed=embed)
        await spoiler_msg.add_reaction(self.qm)
        self.spoilers[str(spoiler_msg.id)] = (title, text, user)
        await user.send('Your Spoiler message was created')


def setup(client):
    """This is called then the cog is loaded via load_extension"""
    client.add_cog(Spoiler(client))
