"""This is a cog for a discord.py bot.
It will provide commands to jail users
and auto jail users for excessive messaging.

Commands:
    jail                Jail a @user
    unjail              Release a @user from jail

Only users that have an admin role can use the commands.
"""

from discord.ext import commands
from discord import Member
import asyncio
import json
import time

# SETTINGS:
# TODO: Ideally these settings sould also come from the config.json file
# Users will receive a warning if they send more than
SPAM_NUM_MSG = 5  # Messages
# Within
SPAM_TIME = 10  # Seconds
# If a user receives a second warning within
SPAM_NAUGHTY_DURATION = 900  # Seconds
# he will be permanently jailed
# The task that clears the history and removes users from the "watchlist" if
# they have been on it for more than SPAM_NAUGHTY_DURATION will run every
SPAM_NAUGHTY_CHECK_INTERVAL = 300  # seconds


class Jail(commands.Cog, name='Jail'):
    def __init__(self, client):
        self.client = client
        self.jail_roles = self.client.config['jail_roles']
        # Dict to store offenders
        self.naughty = {}
        # Dict to store the timestamps of each users last 10 messages
        self.history = {}
        # Task that will remove users from the naughty list if they behaved for
        # 15 minutes - will also clear self.history to not let it get too big
        self.my_task = self.client.loop.create_task(self.clear_naughty_list())

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

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

    async def send_to_jail(self, member, reason=None, permanent=True):
        """Jail a user

        Arguments:
            member {discord.Member} -- The Member to jail

        Keyword Arguments:
            reason {string} -- The Reason that will show in the
                               Audit Log (default: {None})
            permanent {bool} -- Add the users id to the
                                state.json (default: {True})

        Returns:
            str -- Status message
        """
        status = 'Success'
        get_role = member.guild.get_role
        jail_roles = [get_role(x) for x in self.jail_roles if get_role(x)]
        await member.add_roles(*jail_roles, reason=reason)
        if permanent:
            perma_jail = self.load_perma_jail()
            if member.id not in perma_jail:
                perma_jail.append(member.id)
                self.save_perma_jail(perma_jail)
            else:
                status = f'{member} is already jailed'
        return status

    async def release_from_jail(self, member):
        """Un-Jail a user

        Arguments:
            member {discord.Member} -- The Member to un-jail

        Returns:
            str -- Status message
        """
        status = 'Success'
        perma_jail = self.load_perma_jail()
        get_role = member.guild.get_role
        jail_roles = [get_role(x) for x in self.jail_roles if get_role(x)]
        await member.remove_roles(*jail_roles)
        if member.id in perma_jail:
            perma_jail.remove(member.id)
            self.save_perma_jail(perma_jail)
        else:
            status = f'{member} is not in jail'
        return status

    # ----------------------------------------------
    # Cog Event listeners
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, msg):
        member = msg.author
        if member == self.client.user:
            # Don't run on the bots own messages
            return
        now = time.time()
        uid = str(member.id)
        user_history = self.history.get(uid, [])
        # Add timestamp of current message to list of known timestamps of user
        user_history.append(now)
        if len(user_history) == SPAM_NUM_MSG:
            # When we know enough message timestamps (SPAM_NUM_MSG)
            # Pop the oldest message
            oldest = user_history.pop(0)
            if now - oldest < SPAM_TIME:
                # If the oldest message was sent less than SPAM_TIME seconds ago
                if uid in self.naughty:
                    # Jail the user permanently
                    # If he is already on the naughty list
                    await self.send_to_jail(member,
                                            reason='Excessive messaging')
                    await msg.channel.send("Aaaand it's gone")
                else:
                    # Warn the user and add him to the naughty list
                    # If he is not on the naughty list yet
                    await msg.channel.send(
                        f'Hey {member.mention}, you are sending too many ' +
                        'messages. This is a warning! If you keep ' +
                        'this up you will be jailed.'
                    )
                    self.naughty[uid] = now
                    # "Reset" his history so he doesn't get jailed immediately
                    # on the 11th message
                    user_history = []
        # Save the users history again (the oldest message was popped)
        self.history[uid] = user_history

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Checks if a joining user is "perma-jailed"
        and jails him if needed
        """
        perma_jail = self.load_perma_jail()
        if member.id in perma_jail:
            await self.send_to_jail(
                member, reason='User tried to rejoin', permanent=False
            )

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.command(
        name='jail',
        aliases=['silence'],
        hidden=True,
    )
    async def jail(self, ctx, members: commands.Greedy[Member]):
        """Put a list of @users in jail"""
        if not members:
            raise commands.BadArgument('Please specify at least 1 member')
        results = []
        for member in members:
            if self.client.user_is_admin(member):
                results.append(f'Sorry {member} is my friend')
            else:
                r = await self.send_to_jail(member)
                results.append(r)
        await ctx.send('```\n'+'\n'.join(results)+'```')

    @commands.command(
        name='unjail',
        aliases=['release', 'unsilence'],
        hidden=True,
    )
    async def unjail(self, ctx, members: commands.Greedy[Member]):
        """Release a list of @users from jail"""
        if not members:
            raise commands.BadArgument('Please specify at least 1 member')
        results = []
        for member in members:
            r = await self.release_from_jail(member)
            results.append(r)
        await ctx.send('```\n'+'\n'.join(results)+'```')

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------
    async def clear_naughty_list(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        try:
            while not self.client.is_closed():
                now = time.time()
                newdict = {}
                for k, v in self.naughty.items():
                    if now - v < SPAM_NAUGHTY_DURATION:
                        newdict[k] = v
                self.naughty = newdict
                self.history = {}
                await asyncio.sleep(SPAM_NAUGHTY_CHECK_INTERVAL)
        except asyncio.CancelledError:
            pass

    def cog_unload(self):
        self.my_task.cancel()


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Jail(client))
