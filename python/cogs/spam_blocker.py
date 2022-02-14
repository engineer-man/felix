"""This is a cog for a discord.py bot.
It will provide commands to jail users for sending spam phishing links.

Commands:
    spam        Commands to add/remove to spam list
    ├ add       add spam link to automatically jails a user if posted
    ├ create    create spam database
    ├ drop      drop spam database
    ├ remove    remove a spam link that automatically jails a user if posted
    ├ update    todo -> edit/update existing by rule id
    ├ who       Show who created the rule
    └ list      show list of all spam links

Only users that have an admin role can use the commands.
"""

import asyncio
import re
import json

from db.config import engine, Base, async_session
from db.models.dals import  SpamDAL, SpammerDAL

from discord.ext import commands, tasks
from discord import Member, DMChannel, Embed, NotFound



class SpamBlocker(commands.Cog, name='Spam'):
    def __init__(self, client):
        self.client = client
        self.jail_roles = self.client.config['jail_roles']
        self.REPORT_CHANNEL_ID = self.client.config['report_channel']
        self.JAIL_CHANNEL_ID = self.client.config['jail_channel']
        self.REPORT_ROLE = self.client.config['report_role']
        self.TEAM_ROLE = self.client.config['team_role']
        # Dict to load spam rules from db
        self.loop_get = asyncio.get_event_loop()
        self.spam_dict = self.loop_get.run_until_complete(self.construct_spam_dict())
        

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

    async def construct_spam_dict(self):
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
            return {rule.regex:re.compile(rule.regex) for rule in await scd.get_all_spam()}

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

    async def post_report(self, msg):
        """Post report of auto jailing to report channel"""
        target = self.client.get_channel(self.REPORT_CHANNEL_ID)
        await target.send(
            f'<@&{self.REPORT_ROLE}> I jailed a user\n'
            f'User {msg.author.mention} spammed in {msg.channel.mention}'
        )
        return True

    async def post_spam_report(self, msg, matched_line):
        """Post spam report of auto jailing to report channel"""
        target = self.client.get_channel(self.REPORT_CHANNEL_ID)
        embed = Embed(
            title='Phishing Link Detected!',
            description=f'{msg.content}\nRule: `{matched_line}`',
            color=0xFFFFFF
        )
        await target.send(
            f'<@&{self.REPORT_ROLE}> I jailed a user\n'
            f'User {msg.author.mention} spammed in {msg.channel.mention}',
            embed=embed
        )
        return True

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

        if self.spam_dict and msg.channel.id != self.JAIL_CHANNEL_ID:
            for regex_string, regex in self.spam_dict.items():
                if regex.findall(msg.content):
                    await self.send_to_jail(member, reason='Sent illegal spam')
                    await self.post_spam_report(msg, regex_string)
                    await msg.delete()
                    break


    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.group(
        pass_context=True,
        name='spam',
        hidden=True,
        invoke_without_command=True,
    )
    async def spam(self, ctx):
        "Commands to add/remove to spam list"
        await ctx.send_help('spam')

    @spam.command(
        name='create',
        aliases=['initdb']
    )
    async def create_spam_db(self, ctx):
        """Initiate A Spam Database"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await ctx.send(f'✅ Spam Database Created!')

    @spam.command(
        name='drop',
    )
    async def drop_spam_db(self, ctx):
        """Drop/Remove existing Spam Database"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await ctx.send(f'✅ Spam Database Dropped!')

    @spam.command(
        name='add',
        aliases=['a', 'new']
    )
    async def add_spam(self, ctx, regex: str):
        """Add spam link to automatically jail a user if posted"""
        member = ctx.message.author
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                await scd.add_spam(member.id, regex)
                user = await self.client.fetch_user(member.id)
                # update self.spam_dict
                self.spam_dict[regex] = re.compile(regex)

            embed = Embed(
                color=0x13DC51,
                title=f'New Phishing Rule Added',
                description=f'```✅ {regex}```',
            )
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_footer(
                text=member.name,
                icon_url=member.display_avatar
            )
            await ctx.send(embed=embed)

    @spam.command(
        name='list',
        aliases=['ls', 'sl']
    )
    async def current_spam_list(self, ctx):
        """List of current items in spam list items"""
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                res = await scd.get_all_spam()
                NUM_SPAM = 25
                NUM_LEN = 25
                all_spam = [f'{row.id} | {row.regex}' for row in res]
                response = []
                for _ in range(len(all_spam)):
                    response.append('\n'.join(all_spam[NUM_SPAM - NUM_LEN:NUM_SPAM]))
                    NUM_SPAM += NUM_LEN
                for block in response:
                    await ctx.send(f'```{"".join(block)}```') if len(block) > 0 else None

    @spam.command(
        name='who',
        aliases=['w']
    )
    async def spam_added_by(self, ctx, _id: str):
        """Show who added spam link"""
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                row = await scd.spam_by_id(_id)
                user = await self.client.fetch_user(row.member)

            embed = Embed(
                color=0x59E685,
                title=f'Rule {row.id} | Added By {user.name}',
                description=f'```Rule: {row.regex}```',
            )
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_footer(
                text=user.name,
                icon_url=user.display_avatar
            )
            await ctx.send(embed=embed)

    @spam.command(
        name='remove',
        aliases=['rm']
    )
    async def remove_spam_item(self, ctx, _id:int):
        """Remove item from spam list by ID"""
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                row = await scd.spam_by_id(_id)
                await scd.delete_spam(_id)
                user = await self.client.fetch_user(row.member)
                # update self.spam_dict
                self.spam_dict.pop(row.regex)


            embed = Embed(
                color=0xA0F1B9,
                title=f'Rule {row.id} | Deleted By {user.name}',
                description=f'```❌ {row.regex}```',
            )
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_footer(
                text=user.name,
                icon_url=user.display_avatar
            )
            await ctx.send(embed=embed)


    @spam.command(
        name='show',
        aliases=['s']
    )
    async def show_dict(self, ctx):
        """Show raw list for testing..."""
        await ctx.send(f'```Check Coroutine Output...\n{self.spam_dict}```')                              


    '''
    @spam.command(
        name='update',
        aliases=['mv'],
    )
    async def update_regex_rule(self, ctx, *, _id:int, rule:str):
        #await ctx.send(f'{_id}, {type(_id)} | {ctx.message.author.id}, {type(ctx.message.author.id)} | {rule}, {type(rule)}')
        """Update spam rule, by id new_rule"""
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                member = ctx.message.author.id
                await scd.update_spam_rule(_id, member, rule)
            await ctx.send(f'✅ {_id} | {rule} Updated!')
    '''

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(SpamBlocker(client))
