from discord.ext import commands, tasks
#pylint: disable=E1101

class MyName(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client
        self.get_my_name_back.start()
        self.REPORT_CHANNEL = self.client.get_channel(483979023144189966)

    @tasks.loop(minutes=1)
    async def get_my_name_back(self):
        try:
            await self.client.user.edit(username='Felix')
            await self.REPORT_CHANNEL.send('Got my name back')
            self.get_my_name_back.cancel()
        except Exception as e:
            await self.REPORT_CHANNEL.send(str(e))

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(MyName(client))
