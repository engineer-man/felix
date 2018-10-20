"""This is a cog for a discord.py bot.
It will provide commands to jail users
and auto jail users for excessive messaging.

Commands:
    jail                Jail a @user
    unjail, release     Release a @user from jail
"""

from discord.ext import commands
from discord import Member
from os import path
import asyncio
import json


class Jail():
    def __init__(self, client):
        self.client = client
        self.my_task = self.client.loop.create_task(self.jail_task())
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            self.permitted_roles = json.load(f)[__name__.split('.')[-1]]
        self.jail_roles = [486621918821351436,
                           484183734686318613,
                           484016038992674827,
                           503226565157715998]  # TODO REMOVE
        self.naughty = {}

    async def __local_check(self, ctx):
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    # ----------------------------------------------
    # Helper Functions
    # ----------------------------------------------

    def load_state(self):
        with open("../state.json", "r") as statefile:
            return json.load(statefile)

    def load_perma_jail(self):
        state = self.load_state()
        return state.get('jailed', [])

    def save_perma_jail(self, perma_jail):
        state = self.load_state()
        state['jailed'] = perma_jail
        with open("../state.json", "w") as statefile:
            return json.dump(state, statefile, indent=1)

    async def send_to_jail(self, member, reason='', permanent=False):
        get_role = member.guild.get_role
        jail_roles = [get_role(x) for x in self.jail_roles if get_role(x)]
        await member.add_roles(*jail_roles, reason=reason)
        if permanent:
            perma_jail = self.load_perma_jail()
            if member.id not in perma_jail:
                perma_jail.append(member.id)
                self.save_perma_jail(perma_jail)
        return 'Success'


    async def release_from_jail(self, member):
        perma_jail = self.load_perma_jail()
        if member.id not in perma_jail:
            return f'{member} is not jailed'
        get_role = member.guild.get_role
        jail_roles = [get_role(x) for x in self.jail_roles if get_role(x)]
        await member.remove_roles(*jail_roles)
        perma_jail.remove(member.id)
        self.save_perma_jail(perma_jail)
        return 'Success'


    # ----------------------------------------------
    # Cog Event listeners
    # ----------------------------------------------
    async def on_message(self, msg):
        print(msg.content)

    async def on_member_join(self, member):
        perma_jail = self.load_perma_jail()
        if member.id in perma_jail:
            await self.send_to_jail(member, reason='User tried to rejoin')

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.command(
        name='jail',
        brief='Put a @user in jail',
        description='Put a @user in jail',
        aliases=['silence'],
        hidden=True,
    )
    @commands.guild_only()
    async def jail(self, ctx, member: Member):
        r = await self.send_to_jail(member, permanent=True)
        await ctx.send(r)

    @commands.command(
        name='unjail',
        brief='Release a @user from jail',
        description='Release a @user from jail',
        aliases=['release', 'unsilence'],
        hidden=True,
    )
    @commands.guild_only()
    async def unjail(self, ctx, member: Member):
        r = await self.release_from_jail(member)
        await ctx.send(r)

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------
    async def jail_task(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        try:
            while not self.client.is_closed():
                # print('Running Task')
                await asyncio.sleep(300)
        except asyncio.CancelledError:
            pass

    def __unload(self):
        self.my_task.cancel()


def setup(client):
    """This is called then the cog is loaded via load_extension"""
    client.add_cog(Jail(client))


def teardown(client):
    """This is called then the cog is unloaded via unload_extension"""
    pass
