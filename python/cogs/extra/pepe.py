"""This is Pepe
"""
#pylint: disable=E1101

from discord.ext import commands, tasks

class Pepe(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client
        self.pepeify.start()

    @tasks.loop(count=1)
    async def pepeify(self):
        self.old_prefix = self.client.command_prefix
        self.client.command_prefix = commands.when_mentioned_or('pepe ', 'Pepe ')
        self.old_desc = self.client.description
        self.client.description = 'Hi I am Pepe!'
        self.old_name = self.client.user.name
        await self.client.user.edit(username='Pepe')

    @tasks.loop(count=1)
    async def unpepeify(self):
        self.client.command_prefix = self.old_prefix
        self.client.description = self.old_desc
        await self.client.user.edit(username=self.old_name)

    def cog_unload(self):
        self.unpepeify.start()


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Pepe(client))
