"""This is a cog for a discord.py bot.
It will provide the functionality to give a newcomer role to people joining
and remove it after a certain time
"""

import asyncio
from datetime import datetime
from discord.ext import commands

# SETTINGS:
NEWCOMER_ROLE = 589402753495990274
NEWCOMER_DURATION = 48 * 3600  # seconds
NEWCOMER_CHECK_INTERVAL = 3600  # seconds


class Newcomer(commands.Cog, name='Newcomer'):
    def __init__(self, client):
        self.client = client
        self.my_task = self.client.loop.create_task(self.clear_newcomers())

    # ----------------------------------------------
    # Cog Event listeners
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.guild.id == self.client.main_guild.id:
            return
        await member.add_roles(member.guild.get_role(NEWCOMER_ROLE))

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------
    async def clear_newcomers(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        try:
            while not self.client.is_closed():
                for member in self.client.main_guild.members:
                    if NEWCOMER_ROLE not in [role.id for role in member.roles]:
                        continue
                    join_date = member.joined_at
                    if not join_date:
                        continue
                    current_date = datetime.utcnow()
                    time_delta = (current_date - join_date).total_seconds()
                    if time_delta > NEWCOMER_DURATION:
                        await member.remove_roles(
                            member.guild.get_role(NEWCOMER_ROLE)
                        )
                await asyncio.sleep(NEWCOMER_CHECK_INTERVAL)
        except asyncio.CancelledError:
            pass

    def cog_unload(self):
        self.my_task.cancel()


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Newcomer(client))
