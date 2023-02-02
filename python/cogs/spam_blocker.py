"""This is a cog for a discord.py bot.
It will provide commands to jail users for sending spam phishing links.

Commands:
    spam        Commands to add/update/remove to a spam list
    ├ add       add spam link to automatically jails a user if posted
    ├ create    create spam database
    ├ drop      drop spam database
    ├ list      show list of all spam links as text dump
    ├ list 1    show list of spam links as paginated embed
    ├ remove    remove a spam link that automatically jails a user if posted
    ├ test      test if string matches an existing rule
    ├ update    update/edit existing spam rule by rule id
    └ who       Show who created the rule

    spammer
    └ list      last 10 spam rule breakers in desc order

Only users that have an admin role can use the commands.
"""

import re
import json
from io import BytesIO

from db.config import engine, Base, async_session
from db.models.dals import SpamDAL, SpammerDAL

from discord.ext import commands, tasks
from discord import DMChannel, Member, Embed, NotFound, File


class SpamBlocker(commands.Cog, name='Spam'):
    def __init__(self, client):
        self.client = client
        self.jail_roles = self.client.config['jail_roles']
        self.REPORT_CHANNEL_ID = self.client.config['report_channel']
        self.JAIL_CHANNEL_ID = self.client.config['jail_channel']
        self.REPORT_ROLE = self.client.config['report_role']
        self.TEAM_ROLE = self.client.config['team_role']
        self.spam_dict = None
        # init database and tables
        self.init_database.start()
        self.construct_spam_dict.start()


    @tasks.loop(count=1)
    async def init_database(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


    @tasks.loop(count=1, reconnect=True)
    async def construct_spam_dict(self):
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                rows = await scd.get_all_spam()
            self.spam_dict = {rule.regex: re.compile(rule.regex, re.I) for rule in rows}


    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    # ----------------------------------------------
    # Helper Functions
    # ----------------------------------------------
    def reload_spam_dict(self):
        self.construct_spam_dict.stop()
        self.construct_spam_dict.start()

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
                    async with async_session() as db:
                        async with db.begin():
                            scd = SpammerDAL(db)
                            await scd.add_spammer(member=member.id, regex=regex_string)
                    await msg.delete()
                    break


    # ----------------------------------------------
    # Spam Cog Commands
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
        name='reset'
    )
    async def rebuild_spam_db(self, ctx):
        """WARNING!!! this will drop all tables and recreate them"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            self.spam_dict = None
        await ctx.send(f'```✅ Spam Database reinitialized!```')


    @spam.command(
        name='add',
        aliases=['new']
    )
    async def add_spam(self, ctx, *args):
        """Add a spam link to automatically jail a user if posted"""
        regex = ' '.join((x for x in args))
        member = ctx.message.author
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                # check rule not already in database before adding.
                check_dupe = await scd.check_duplicate(regex)
                if check_dupe:
                    await ctx.send(f'```❌ Sorry {member.name}, {regex} is already in spam database!```')
                    return
                # commit new spam rule and return updated rule set
                rows = await scd.add_spam(member.id, regex)
                self.spam_dict = {rule.regex:re.compile(rule.regex, re.I) for rule in rows}

                embed = Embed(
                    color=0x13DC51,
                    title=f'New Phishing Rule Added',
                    description=f'```✅ {regex}```',
                )
                embed.set_footer(
                    text=member.name,
                    icon_url=member.display_avatar
                )
                await ctx.send(embed=embed)


    @spam.command(
        name='remove',
        aliases=['rm']
    )
    async def remove_spam_item(self, ctx, _id:int):
        """Remove an item from spam list by its ID"""
        member = ctx.message.author
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                row = await scd.spam_by_id(_id)
                if not row:
                    await ctx.send(f'```❌ Sorry {member.name}, cannot remove Rule {_id} it does not exist!```')
                    return
                await scd.delete_spam(_id)
                # reload spam dict on item removal
                self.reload_spam_dict()

            embed = Embed(
                color=0xA0F1B9,
                title=f'Rule {row.id} | Removed By {member.name}',
                description=f'```❌ {row.regex}```'
            )
            embed.set_footer(
                text=member.name,
                icon_url=member.display_avatar
            )
            await ctx.send(embed=embed)


    @spam.command(
        name='update',
        aliases=['mv'],
    )
    async def update_regex_rule(self, ctx, _id, *args):
        """Update an existing spam rule by rule ID"""
        regex = ' '.join((x for x in args))
        member = ctx.message.author
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                await scd.update_spam_rule(_id, member.id, regex)
                # reload spam dict on change
                self.reload_spam_dict()

            embed = Embed(
                color=0xA0F1B9,
                title=f'Rule {_id} | Updated By {member.name}',
                description=f'```✅ {regex}```'
            )
            embed.set_footer(
                text=member.name,
                icon_url=member.display_avatar
            )
            await ctx.send(embed=embed)


    @spam.command(
        name='list',
        aliases=['ls']
    )
    async def current_spam_list(self, ctx, _paginate=False):
        """Lists all current items in the spam database"""
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                res = await scd.get_all_spam()

            all_spam = '\n'.join(f'{row.id:4} | {row.regex}' for row in res)

        if not _paginate:
            return await ctx.send(
                file=File(BytesIO(all_spam.encode()), filename='spam-ls.txt'),
                content=f'Hey {ctx.message.author.name}, Here is the current spam list...'
            )

        paginator = commands.Paginator(prefix='```', suffix='```', linesep='\n', max_size=2000)
        for line in all_spam.split('\n'):
            paginator.add_line(line)
        message = None

        for page in paginator.pages:
            await ctx.send(page)

        paginator.clear()
        return message


    @spam.command(
        name='who',
        aliases=['w']
    )
    async def spam_added_by(self, ctx, _id: str):
        """Show who added spam link by ID"""
        member = ctx.message.author
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                row = await scd.spam_by_id(_id)
                if not row:
                    await ctx.send(f'```❌ Sorry {member.name}, Rule: {_id} does not exist!```')
                    return

            user = await self.client.fetch_user(row.member)
            embed = Embed(
                color=0x59E685,
                title=f'Rule {row.id} | Created By {user.name}',
                description=f'```Rule: {row.regex}```',
            )
            embed.set_footer(
                text=user.name,
                icon_url=user.display_avatar
            )
            await ctx.send(embed=embed)


    @spam.command(
        name="test",
        aliases=["t", "teststring"]
    )
    async def spam_test(self, ctx, *args):
        """Test a string and see what rules it matches"""
        member = ctx.message.author
        test_string = ' '.join((x for x in args))
        matches = []
        spam_id = None
        async with async_session() as db:
            async with db.begin():
                scd = SpamDAL(db)
                all_spam = await scd.get_all_spam()

        for regex_string, regex in self.spam_dict.items():
            if regex.findall(test_string):
                for spam in all_spam:
                    if spam.regex == regex_string:
                        spam_id = spam.id
                matches.append({'str': regex_string, 'id': spam_id})
            spam_id = None

        if len(matches) == 0:
            await ctx.send(f"Hey {member.name}, No rule matches for: `{test_string}`")
            return

        msg = f"""```\nMatches {len(matches)} rule{'s' if len(matches) > 1 else ''}: """
        for match in matches[:10]:
            msg += f"\n {match.get('id'):4} | {match.get('str')}"
        msg += "\n```"
        await ctx.send(msg)

    # ----------------------------------------------
    # Spammer Cog Commands
    # ----------------------------------------------
    @commands.group(
        pass_context=True,
        name='spammer',
        hidden=True,
        invoke_without_command=True,
    )
    async def spammer(self, ctx):
        "Commands to view spam rule breakers"
        await ctx.send_help('spammer')


    @spammer.command(
        name='count',
        aliases=['c', 'number']
    )
    async def rule_breaker_count(self, ctx):
        """Show a count of rule breakers"""
        async with async_session() as db:
            async with db.begin():
                scd = SpammerDAL(db)
                count = await scd.get_spammer_count()

        embed = Embed(
            title='Total Scammers',
            description=f'```I have yeeted {count} scammers so far. you\'re welcome!```',
            color=0xFFFFFF
        )
        await ctx.send(embed=embed)


    @spammer.command(
        name='list',
        aliases=['ls']
    )
    async def list_rule_breakers(self, ctx):
        """Last 10 Rule Breakers and Rule Desc order"""
        async with async_session() as db:
            async with db.begin():
                scd = SpammerDAL(db)
                rows = await scd.get_all_spammers()
                NUM_SPAM = 10
                NUM_LEN = 10
                all_spammers = [f' {row.id} | {await self.client.fetch_user(row.member)} | {row.regex}' for row in rows]
                response = []
                for _ in range(len(all_spammers)):
                    response.append('\n'.join(all_spammers[NUM_SPAM - NUM_LEN:NUM_SPAM]))
                    NUM_SPAM += NUM_LEN
                for block in response:
                    await ctx.send(f'```{"".join(block)}```') if len(block) > 0 else None


    @spammer.command(
        name='remove',
        aliases=['rm']
    )
    async def remove_spammer_item(self, ctx, _id:int):
        """Remove an item from spam list by its ID"""
        member = ctx.message.author
        async with async_session() as db:
            async with db.begin():
                scd = SpammerDAL(db)
                row = await scd.spammer_by_id(_id)
                if not row:
                    await ctx.send(f'```❌ Sorry {member.name}, cannot remove spammer {_id} it does not exist!```')
                    return
                await scd.delete_spammer(_id)

            embed = Embed(
                color=0xA0F1B9,
                title=f'Spammer {row.id} | Removed By {member.name}',
                description=f'```✅ {await self.client.fetch_user(row.member)} removed from list.```'
            )
            embed.set_footer(
                text=member.name,
                icon_url=member.display_avatar
            )
            await ctx.send(embed=embed)


    @spammer.command(
        name='search',
        aliases=['user', 'history']
    )
    async def spammer_search(self, ctx, member: Member = None):
        """Search member name to see if they have been caught phishing before."""
        member_id = member.id
        async with async_session() as db:
            async with db.begin():
                scd = SpammerDAL(db)
                res = await scd.search_spammer(member_id)
                if not res:
                    embed = Embed(
                        color=0x13DC51,
                        title='Criminal History Check',
                        description=f'```{await self.client.fetch_user(member_id)} is clean.```'
                    )
                    return await ctx.send(embed=embed)

        rules_broken = '\n'.join([
            f'{row.id} | ' +
            f'{await self.client.fetch_user(row.member)} | ' +
            f'{row.regex}' for row in res
        ])
        embed = Embed(
            color=0x13DC51,
            title='Criminal History Check',
            description=f'```{rules_broken}```'
        )
        return await ctx.send(embed=embed)


    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------

async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(SpamBlocker(client))
