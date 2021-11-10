"""This is a cog for a discord.py bot.
It will provide commands to jail users
and auto jail users for excessive messaging.
It also includes commands to handle server flooding.

Commands:
    flood       print flood help message
    ├ list      print list of suspected flooders
    ├ jailall   jail all suspected flooders
    └ clear     clear the suspected flooder list

    jail        Jail a @user
    unjail      Release a @user from jail

    spam        add known bad spam link to jail a user if posted
    rmspam      remove incorrectly added spam link
    spamlist    show list of all spam links in spam

Only users that have an admin role can use the commands.
"""

import re
import json
import time
from collections import deque
from dataclasses import dataclass, field
from discord.ext import commands, tasks
from discord import Member, DMChannel, Embed, NotFound, VerificationLevel
#pylint: disable=E1101


# SETTINGS:
# Users will receive a warning if they send more than
SPAM_NUM_MSG = 7  # Messages
# Within
SPAM_TIME = 10  # Seconds
# If a user receives a second warning within
SPAM_NAUGHTY_DURATION = 900  # Seconds
# he will be permanently jailed
# The task that clears the history and removes users from the "watchlist" if
# they have been on it for more than SPAM_NAUGHTY_DURATION will run every
SPAM_NAUGHTY_CHECK_INTERVAL = 300  # seconds
# Staff will recieve a warning if more than
FLOOD_JOIN_NUM = 10  # Users join
# Within
FLOOD_JOIN_TIME = 10  # Seconds
# And the servers verification level will be changed to
# available options: none, medium, high, extreme
FLOOD_VERIFICATION_LEVEL = VerificationLevel.extreme
# The default verification level is
DEFAULT_VERIFICATION_LEVEL = VerificationLevel.medium


@dataclass
class PendingAcceptance:
    condition: str
    users: list = field(default_factory=list)


class Jail(commands.Cog, name='Jail'):
    def __init__(self, client):
        self.client = client
        self.jail_roles = self.client.config['jail_roles']
        self.REPORT_CHANNEL_ID = self.client.config['report_channel']
        self.JAIL_CHANNEL_ID = self.client.config['jail_channel']
        self.REPORT_ROLE = self.client.config['report_role']
        self.TEAM_ROLE = self.client.config['team_role']
        # Dict to store offenders
        self.naughty = {}
        # Dict to store the timestamps of each users last 10 messages
        self.history = {}
        self.member_history = deque(
            [(time.time() - FLOOD_JOIN_TIME, None)] * FLOOD_JOIN_NUM,
            FLOOD_JOIN_NUM
        )
        self.suspected_flooders = set()
        # Task that will remove users from the naughty list if they behaved for
        # 15 minutes - will also clear self.history to not let it get too big
        self.clear_naughty_list.start()
        self.acceptance_pending = dict()
        # initalise a spam list
        self._spam_list = None
        # Compile initial spam list for regex if list available
        self.is_spam = re.compile('|'.join(x for x in self.load_perma_spam()), re.IGNORECASE)

    @property
    def spam_list(self):
        if self._spam_list is None:
            self._spam_list = self.load_perma_spam()
        return self._spam_list


    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)


    # ----------------------------------------------
    # Helper Functions
    # ----------------------------------------------
    async def report_flood(self):
        target = self.client.get_channel(self.REPORT_CHANNEL_ID)
        description = (
            f'More than {FLOOD_JOIN_NUM} users joined within {FLOOD_JOIN_TIME} '
            'seconds.\n**I have disabled welcome messages and set the verification '
            f'level to "highest"**.\n'
            'Options:\n • `felix flood list` to see the usernames\n'
            '• `felix flood clear` to clear the list, enable welcome messages '
            'and reset the verification level to "medium".'
        )
        embed = Embed(
            title='Warning!',
            description=description,
            color=0xFF0000
        )
        await target.send(f'<@&{self.TEAM_ROLE}>', embed=embed)

    async def enable_flood_mode(self):
        await self.client.main_guild.edit(
            verification_level=FLOOD_VERIFICATION_LEVEL
        )
        self.client.flood_mode = True

    async def disable_flood_mode(self):
        await self.client.main_guild.edit(
            verification_level=DEFAULT_VERIFICATION_LEVEL
        )
        self.client.flood_mode = False

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

    def load_perma_spam(self):
        state = self.load_state()
        return state.get('spam', [])

    def save_perma_spam(self, perma_spam):
        state = self.load_state()
        state['spam'] = perma_spam
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
        status = f'{member} successfully jailed'
        get_role = member.guild.get_role
        jail_roles = [get_role(x) for x in self.jail_roles if get_role(x)]
        try:
            await member.add_roles(*jail_roles, reason=reason)
        except NotFound:
            status = f'{member} not in guild'
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
        status = f'{member} successfully released'
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

    async def post_report(self, msg):
        """Post report of auto jailing to report channel"""
        target = self.client.get_channel(self.REPORT_CHANNEL_ID)
        await target.send(
            f'<@&{self.REPORT_ROLE}> I jailed a user\n'
            f'User {msg.author.mention} spammed in {msg.channel.mention}'
        )
        return True

    async def post_spam_report(self, msg):
        """Post spam report of auto jailing to report channel"""
        target = self.client.get_channel(self.REPORT_CHANNEL_ID)
        embed = Embed(
            title='Phishing Link Detected!',
            description=msg.content,
            color=0xFFFFFF
        )
        await target.send(
            f'<@&{self.REPORT_ROLE}> I jailed a user\n'
            f'User {msg.author.mention} spammed in {msg.channel.mention}',
            embed=embed
        )
        return True

    async def send_to_spam(self, spam):
        status = f'{spam} successfully added to spam list'
        perma_spam = self.load_perma_spam()
        if spam not in perma_spam:
            # add new spam link item to regex list
            perma_spam.append(spam)
            self.spam_list.append(spam)
            self.is_spam = re.compile('|'.join(x for x in perma_spam), re.IGNORECASE)
            # save new spam item to state file
            self.save_perma_spam(perma_spam)
        else:
            status = f'{spam} is already in spam list'
        return status

    async def remove_from_spam(self, spam):
        status = f'{spam} successfully removed from spam list'
        perma_spam = self.load_perma_spam()
        if spam in perma_spam:
            # remove spam list item from regex list
            perma_spam.remove(spam)
            self.spam_list.remove(spam)
            self.is_spam = re.compile('|'.join(x for x in perma_spam), re.IGNORECASE)
            # remove old spam item and save state file
            self.save_perma_spam(perma_spam)
        else:
            status = f'{spam} is not in spam list'
        return status


    # ----------------------------------------------
    # Cog Event listeners
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, msg):
        member = msg.author
        if msg.author.bot:
            # Dont run on any bot messages
            return
        if isinstance(msg.channel, DMChannel):
            # Ignore DM
            return
        if self.client.user_is_admin(member):
            # Dont jail friends on after adding a new spam link
            return

        if self.spam_list:
            # Check we have a spam list available before using it
            if self.is_spam.findall(msg.content) and msg.channel.id != self.JAIL_CHANNEL_ID:
                # Ignore reporting if offender is already in jail for spam
                await self.send_to_jail(member, reason='Sent illegal spam')
                await self.post_spam_report(msg)
                # Clean up and remove message from channel after delay = seconds
                await msg.delete(delay=3)

        now = time.time()
        uid = str(member.id)
        user_history = self.history.get(uid, deque())
        # Add timestamp of current message to list of known timestamps of user
        user_history.append(now)
        if len(user_history) == SPAM_NUM_MSG:
            # When we know enough message timestamps (SPAM_NUM_MSG)
            # Pop the oldest message
            oldest = user_history.popleft()
            if now - oldest < SPAM_TIME:
                # If the oldest message was sent less than SPAM_TIME seconds ago
                if uid in self.naughty:
                    # Jail the user permanently
                    # If he is already on the naughty list
                    await self.send_to_jail(member,
                                            reason='Excessive messaging')
                    await msg.channel.send("Aaaand it's gone")
                    await self.post_report(msg)
                else:
                    # Warn the user and add him to the naughty list
                    # If he is not on the naughty list yet
                    await msg.channel.send(
                        f'Hey {member.mention}, you are sending too many '
                        + 'messages. This is a warning! If you keep '
                        + 'this up you will be jailed.'
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

        # Flood Protection
        now = time.time()
        self.member_history.append((now, member))
        if (now - self.member_history[0][0]) < FLOOD_JOIN_TIME:
            self.suspected_flooders.update(
                member for _, member in self.member_history
            )
            if not self.client.flood_mode:
                await self.report_flood()
                await self.enable_flood_mode()


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        msg = reaction.message

        if msg.id not in self.acceptance_pending:
            return

        pending = self.acceptance_pending[msg.id]
        if not user.id in pending.users:
            return

        if not reaction.emoji == '✅':
            return

        await self.release_from_jail(user)

        report_channel = self.client.get_channel(self.REPORT_CHANNEL_ID)
        await report_channel.send(
            f'<@&{self.REPORT_ROLE}>\n'
            f'{user.mention} has been released from jail after agreeing to the following condition\n'
            f'`{pending.condition}`\n'
        )

        pending.users.remove(user.id)

        if not pending.users:
            del self.acceptance_pending[msg.id]


    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------

    @commands.group(
        invoke_without_command=True,
        name='flood',
        hidden=True
    )
    async def flood(self, ctx):
        """Commands to handle server flooding"""
        await ctx.send_help('flood')

    @flood.command(
        name='list'
    )
    async def flood_list(self, ctx):
        """Show a list of suspected flooders"""
        if not self.suspected_flooders:
            return await ctx.send('List is empty.')
        members = [str(m) for m in self.suspected_flooders]
        # Print 50 members at a time
        for page in range(len(members) // 50 + 1):
            to_print = '\n'.join(members[page*50:(page+1)*50])
            await ctx.send(f'```\n{to_print}\n```')

    @flood.command(
        name='clear',
        aliases=['clean']
    )
    async def flood_clear(self, ctx):
        """Clears the reported member set"""
        self.suspected_flooders.clear()
        await self.disable_flood_mode()
        await ctx.send('`Cleared`')

    # @flood.command(
    #     name='jailall',
    # )
    # async def flood_jailall(self, ctx):
    #     """Jails all members in the reported member set"""
    #     if not self.suspected_flooders:
    #         return await ctx.send('No members to jail.')
    #     await ctx.send(f'`Jailing {len(self.suspected_flooders)} users (might take a while)`')
    #     jailed = []
    #     for i in self.suspected_flooders:
    #         status = await self.send_to_jail(i, reason='Server flooding')
    #         jailed.append(status)

    #     # Print 20 jail confirmations at a time
    #     for page in range(len(jailed) // 20 + 1):
    #         to_print = '\n'.join(jailed[page*20:(page+1)*20])
    #         await ctx.send(f'```\n{to_print}\n```')

    @flood.command(
        name='simulate'
    )
    async def flood_simulate(self, cty):
        await self.report_flood()
        await self.enable_flood_mode()
    # ------------------------------------------------------

    @commands.command(
        name='jail',
        aliases=['silence', 'yeet', 'rm'],
        hidden=True,
    )
    async def jail(self, ctx, members: commands.Greedy[Member]):
        """Put a list of @users in jail"""
        if not members:
            raise commands.BadArgument('Please specify at least 1 member')
        results = []
        for member in members:
            if member == self.client.user:
                results.append('I refuse to jail myself')
            elif self.client.user_is_admin(member):
                results.append(f'Sorry, {member} is my friend')
            else:
                r = await self.send_to_jail(member)
                results.append(r)
        await ctx.send('```\n'+'\n'.join(results)+'```')

    @commands.command(
        name='unjail',
        aliases=['release', 'unsilence'],
        hidden=True,
    )
    async def unjail(self, ctx, members: commands.Greedy[Member], *, condition: str = None):
        """Release a list of @users from jail"""
        if not members:
            raise commands.BadArgument('Please specify at least 1 member')
        results = []
        if condition is None:
            for member in members:
                r = await self.release_from_jail(member)
                results.append(r)
        else:
            mention_all = ' '.join(member.mention for member in members)
            jail_channel = self.client.get_channel(self.JAIL_CHANNEL_ID)
            accept_text = (
                f'Hey {mention_all},\n'
                'you have broken one or more of our rules with your recent behavior.\n'
                'You will be released if you agree to the following condition:\n'
                f'`{condition}`'
            )
            accept_message = await jail_channel.send(accept_text)
            await accept_message.add_reaction('✅')

            pending = PendingAcceptance(condition=condition)

            for member in members:
                if ctx.channel.id != self.JAIL_CHANNEL_ID:
                    results.append(f'Acceptance message posted for {member.name}')
                pending.users.append(member.id)
            self.acceptance_pending[accept_message.id] = pending

        if results:
            await ctx.send('```\n'+'\n'.join(results)+'```')

    
    @commands.command(
        name='spam',
        aliases=['spamadd'],
        hidden=True,
    )
    async def add_spam(self, ctx, link: str):
        """add spam link to automatically jails a user if posted"""
        results = []
        r = await self.send_to_spam(link)
        results.append(r)
        await ctx.send(f'```\n'+'\n'.join(results)+'```')


    @commands.command(
        name='rmspam',
        aliases=['spamrm'],
        hidden=True,
    )
    async def remove_spam(self, ctx, link: str):
        """remove a spam link that automatically jails a user if posted"""
        results = []
        r = await self.remove_from_spam(link)
        results.append(r)
        await ctx.send(f'```\n'+'\n'.join(results)+'```')


    @commands.command(
        name='spamlist',
        aliases=['spamls'],
        hidden=True,
    )
    async def current_spam_list(self, ctx):
        """show list of all spam links in spam"""
        results = self.spam_list
        NUM_SPAM = 25
        NUM_LEN = 25
        response = []
        for _ in range(len(results)):
            response.append('\n'.join(results[NUM_SPAM - NUM_LEN:NUM_SPAM]))
            NUM_SPAM += NUM_LEN
        for block in response:
            await ctx.send(f'```{"".join(block)}```') if len(block) > 0 else None

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------

    @tasks.loop(seconds=SPAM_NAUGHTY_CHECK_INTERVAL)
    async def clear_naughty_list(self):
        now = time.time()
        newdict = {}
        for k, v in self.naughty.items():
            if now - v < SPAM_NAUGHTY_DURATION:
                newdict[k] = v
        self.naughty = newdict
        self.history = {}

        if self.client.flood_mode:
            target = self.client.get_channel(self.REPORT_CHANNEL_ID)
            await target.send(
                f'<@&{self.TEAM_ROLE}> Flood mode is currently enabled.\n'
                'If the flood is over please run `felix flood clear`'
            )

    def cog_unload(self):
        self.clear_naughty_list.cancel()


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Jail(client))
