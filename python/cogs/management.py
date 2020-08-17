"""This is a cog for a discord.py bot.
It will add some management commands to a bot.

Commands:
    version         show the hash of the latest commit
    load            load an extension / cog
    unload          unload an extension / cog
    reload          reload an extension / cog
    cogs            show currently active extensions / cogs
    list            make felix compute a list
     └duplicates        find duplicate usernames

    pull            pull latest changes from github (superuser only)
    error           print the traceback of the last unhandled error to chat

Only users that have an admin role can use the commands.
"""
import subprocess
import json
import traceback
import typing
from datetime import datetime
from os import path, listdir
from discord import Activity, Embed, Member
from discord.ext import commands


class Management(commands.Cog, name='Management'):
    def __init__(self, client):
        self.client = client
        self.reload_config()

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    @commands.Cog.listener()
    async def on_ready(self):
        loaded = self.client.extensions
        unloaded = [x for x in self.crawl_cogs() if x not in loaded]
        # Cogs without extra in their name should be loaded at startup so if
        # any cog without "extra" in it's name is unloaded here -> Error in cog
        if any('extra' not in cog_name for cog_name in unloaded):
            activity_name = 'ERROR in cog'
            activity_type = 3
        else:
            felix_version = self.get_version_info()[0][:7]
            activity_name = f'on {felix_version}'
            activity_type = 0
        await self.client.change_presence(
            activity=Activity(name=activity_name, type=activity_type)
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.client.main_guild.system_channel.send(
            f'Welcome to the Engineer Man Discord Server, {member.mention}\n'
            'I\'m Felix, the server smart assistant. You can learn more about '
            'what I can do by saying `felix help`. If you want answers to '
            'frequently asked questions about Engineer Man, say `felix faq`. '
            'You can view the server rules in <#484103976296644608>. '
            'Please be kind and decent to one another. '
            'Glad you\'re here!'
        )

    # ----------------------------------------------
    # Error handler
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            par = str(error.param)
            missing = par.split(": ")[0]
            if ':' in par:
                missing_type = ' (' + str(par).split(": ")[1] + ')'
            else:
                missing_type = ''
            await ctx.send(
                f'Missing parameter: `{missing}{missing_type}`' +
                f'\nIf you are not sure how to use the command, try running ' +
                f'`felix help {ctx.command.qualified_name}`'
            )
            return

        if isinstance(error, commands.CheckFailure):
            await ctx.send('Sorry, you are not allowed to run this command.')
            return

        if isinstance(error, commands.BadArgument):
            # It's in an embed to prevent mentions from working
            embed = Embed(
                title='Error',
                description=str(error),
                color=0x2ECC71
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.UnexpectedQuoteError):
            await ctx.send('`Unexpected quote encountered`')
            return

        # In case of an unhandled error -> Save the error + current datetime + ctx + original text
        # so it can be accessed later with the error command
        await ctx.send('Sorry, something went wrong. The Error was saved - we will look into it.')
        self.client.last_errors.append((error, datetime.utcnow(), ctx, ctx.message.content))
        await self.client.change_presence(
            activity=Activity(name='ERROR encountered', url=None, type=3)
        )

        print(f'Ignoring exception in command {ctx.command}:', flush=True)
        traceback.print_exception(
            type(error), error, error.__traceback__
        )
        print('-------------------------------------------------------------', flush=True)

    def reload_config(self):
        with open("../config.json") as conffile:
            self.client.config = json.load(conffile)

    def get_version_info(self):
        version = 'unknown'
        date = 'unknown'
        try:
            gitlog = subprocess.check_output(
                ['git', 'log', '-n', '1', '--date=iso']).decode()
            for line in gitlog.split('\n'):
                if line.startswith('commit'):
                    version = line.split(' ')[1]
                elif line.startswith('Date'):
                    date = line[5:].strip()
                    date = date.replace(' +', '+').replace(' ', 'T')
                else:
                    pass
        except Exception as e:
            self.client.last_errors.append((e, datetime.utcnow(), None))
            raise e
        return (version, date)

    async def get_remote_commits(self):
        last_commit = self.get_version_info()[0]
        ext = f'?per_page=10&sha=master'
        repo = 'engineer-man/felix'
        nxt = f'https://api.github.com/repos/{repo}/commits{ext}'
        repo_data = []
        repo_shas = []
        while last_commit not in repo_shas:
            async with self.client.session.get(nxt) as response:
                r = await response.json()
            repo_data += r
            repo_shas = [x['sha'] for x in repo_data]
            try:
                nxt = r.links['next']['url']
            except:
                nxt = ''
        num_comm = repo_shas.index(last_commit)
        return (num_comm, repo_data[0:(num_comm if num_comm > 10 else 10)])

    def crawl_cogs(self, directory='cogs'):
        cogs = []
        for element in listdir(directory):
            if element == 'samples':
                continue
            abs_el = path.join(directory, element)
            if path.isdir(abs_el):
                cogs += self.crawl_cogs(abs_el)
            else:
                filename, ext = path.splitext(element)
                if ext == '.py':
                    dot_dir = directory.replace('\\', '.')
                    dot_dir = dot_dir.replace('/', '.')
                    cogs.append(f'{dot_dir}.' + filename)
        return cogs

    # ----------------------------------------------
    # Function to disply the version
    # ----------------------------------------------
    @commands.command(
        name='version',
        brief='Show current version of felix',
        description='Show current version and changelog of felix',
        hidden=True,
    )
    async def version(self, ctx):
        await ctx.trigger_typing()
        version, date = self.get_version_info()
        num_commits, remote_data = await self.get_remote_commits()
        status = "I am up to date with 'origin/master'"
        changelog = 'Changelog:\n'
        if num_commits:
            status = f"I am [{num_commits}] commits behind 'origin/master'"\
                f" [{remote_data[0]['commit']['author']['date']}]"
        for i, commit in enumerate(remote_data):
            commitmessage = commit['commit']['message']
            if 'merge pull' in commitmessage.lower():
                continue
            changelog += ('+ ' if i < num_commits else '* ')  \
                + commitmessage.split('\n')[0] + '\n'
        await ctx.send(
            f'```css\nCurrent Version: [{version[:7]}].from [{date}]' +
            f'\n{status}``````diff\n{changelog}```'
        )

    # ----------------------------------------------
    # Function to load extensions
    # ----------------------------------------------
    @commands.command(
        name='load',
        brief='Load bot extension',
        description='Load bot extension\n\nExample: felix load cogs.stats',
        hidden=True,
    )
    async def load_extension(self, ctx, extension_name):
        for cog_name in self.crawl_cogs():
            if extension_name in cog_name:
                target_extension = cog_name
                break
        try:
            self.client.load_extension(target_extension)
        except Exception as e:
            self.client.last_errors.append((e, datetime.utcnow(), ctx))
            await ctx.send(f'```py\n{type(e).__name__}: {str(e)}\n```')
            return
        await ctx.send(f'```css\nExtension [{target_extension}] loaded.```')

    # ----------------------------------------------
    # Function to unload extensions
    # ----------------------------------------------
    @commands.command(
        name='unload',
        brief='Unload bot extension',
        description='Unload bot extension\n\nExample: felix unload cogs.stats',
        hidden=True,
    )
    async def unload_extension(self, ctx, extension_name):
        for cog_name in self.client.extensions:
            if extension_name in cog_name:
                target_extension = cog_name
                break
        if target_extension.lower() in 'cogs.management':
            await ctx.send(
                f"```diff\n- {target_extension} can't be unloaded" +
                f"\n+ try felix reload {target_extension}!```"
            )
            return
        if self.client.extensions.get(target_extension) is None:
            return
        self.client.unload_extension(target_extension)
        await ctx.send(f'```css\nExtension [{target_extension}] unloaded.```')

    # ----------------------------------------------
    # Function to reload extensions
    # ----------------------------------------------
    @commands.command(
        name='reload',
        brief='Reload bot extension',
        description='Reload bot extension\n\nExample: felix reload cogs.stats',
        hidden=True,
        aliases=['re']
    )
    async def reload_extension(self, ctx, extension_name):
        target_extensions = []
        if extension_name == 'all':
            target_extensions = [__name__] + \
                [x for x in self.client.extensions if not x == __name__]
        else:
            for cog_name in self.client.extensions:
                if extension_name in cog_name:
                    target_extensions = [cog_name]
                    break
        if not target_extensions:
            return
        result = []
        for ext in target_extensions:
            try:
                self.client.reload_extension(ext)
                result.append(f'Extension [{ext}] reloaded.')
            except Exception as e:
                self.client.last_errors.append((e, datetime.utcnow(), ctx))
                result.append(f'#ERROR loading [{ext}]')
                continue
        result = '\n'.join(result)
        await ctx.send(f'```css\n{result}```')

    # ----------------------------------------------
    # Function to get bot extensions
    # ----------------------------------------------
    @commands.command(
        name='cogs',
        brief='Get loaded cogs',
        description='Get loaded cogs',
        aliases=['extensions'],
        hidden=True,
    )
    async def print_cogs(self, ctx):
        loaded = self.client.extensions
        unloaded = [x for x in self.crawl_cogs() if x not in loaded]
        response = ['\n[Loaded extensions]'] + ['\n  ' + x for x in loaded]
        response += ['\n[Unloaded extensions]'] + \
            ['\n  ' + x for x in unloaded]
        await ctx.send(f'```css{"".join(response)}```')
        return True

    # ----------------------------------------------
    # Function Group to clear channel of messages
    # ----------------------------------------------
    @commands.group(
        invoke_without_command=True,
        name='list',
        hidden=True
    )
    async def _list(self, ctx):
        """List stuff"""
        await ctx.send_help('list')
        return True

    @_list.command(
        name='duplicates'
    )
    async def duplicates(self, ctx):
        """List duplicate usernames"""
        name_count = {}
        aka = {}
        pages = []
        usernames = [(x.name, x.display_name) for x in ctx.guild.members]
        l_max = max([len(x[0]) for x in usernames]) + 1
        for name, display_name in usernames:
            name_count[name] = name_count.get(name, 0) + 1
            if not name == display_name:
                aka[name] = aka.get(name, []) + [display_name]
        page = []
        for key, value in sorted(name_count.items(),
                                 key=lambda x: x[1], reverse=True):
            if value == 1:
                break
            if len('\n'.join(page)) > 1900:
                pages.append(page)
                page = []
            a = ', '.join(aka.get(key, []))
            page.append(f'{value}x {key.ljust(l_max)}' + f'aka: {a}' * bool(a))

        if page:
            pages.append(page)

        if not pages:
            await ctx.send('No duplicate usernames found')

        for n, page in enumerate(pages):
            await ctx.send(f'{n+1}/{len(pages)}\n```' + '\n'.join(page) + '```')

    @_list.command(
        name='earliest'
    )
    async def earliest(self, ctx, n: int = 50, start: int = 0):
        """List  earliest Members"""
        sorted_members = sorted(self.client.main_guild.members, key=lambda x: x.joined_at)
        await ctx.send(
            '```\n' + '\n'.join(f'{x.name} ({x.joined_at.strftime("%Y-%m-%d")})'
                                for x in sorted_members[start:start+n]) + '\n```'
        )

    # ----------------------------------------------
    # Function to get the date a member joined
    # ----------------------------------------------
    @commands.command(
        name='joined',
        hidden=True,
    )
    async def joined(self, ctx, members: commands.Greedy[Member]):
        """Print the date a member joined"""
        if not members:
            raise commands.BadArgument('Please specify at least 1 member')
        await ctx.trigger_typing()
        result = []
        now = datetime.utcnow()
        for member in members:
            join = member.joined_at
            if not join:
                result.append(f'No join date found for {member.name}')
                continue
            difference = now - join
            result.append(
                f'{member.name} joined [{join.isoformat().split(".")[0]}] - '
                f'[{difference.days}] days and '
                f'[{difference.seconds / 3600:.1f}] hours ago'
            )
        if not result:
            return
        await ctx.send('```css\n' + '\n'.join(result) + '\n```')

    @commands.group(
        invoke_without_command=True,
        name='error',
        hidden=True,
        aliases=['errors']
    )
    async def error(self, ctx, n: typing.Optional[int] = None):
        """Show a concise list of stored errors"""

        if n is not None:
            await self.print_traceback(ctx, n)
            return

        NUM_ERRORS_PER_PAGE = 15

        error_log = self.client.last_errors

        if not error_log:
            await ctx.send('Error log is empty')
            return

        response = [f'```css\nNumber of stored errors: {len(error_log)}']
        for i, exc_tuple in enumerate(error_log):
            exc, date, error_source, *_ = exc_tuple
            call_info = (
                f'CMD: {error_source.invoked_with}'
                if isinstance(error_source, commands.Context) else 'outside command'
            )
            response.append(
                f'{i}: ['
                + date.isoformat().split('.')[0]
                + '] - ['
                + call_info
                + f']\nException: {exc}'
            )
            if i % NUM_ERRORS_PER_PAGE == NUM_ERRORS_PER_PAGE-1:
                response.append('```')
                await ctx.send('\n'.join(response))
                response = [f'```css']
        if len(response) > 1:
            response.append('```')
            await ctx.send('\n'.join(response))

    @error.command(
        name='clear',
        aliases=['delete'],
    )
    async def error_clear(self, ctx, n: int = None):
        """Clear error with index [n]"""
        if n is None:
            self.client.last_errors = []
            await ctx.send('Error log cleared')
        else:
            self.client.last_errors.pop(n)
            await ctx.send(f'Deleted error #{n}')

    @error.command(
        name='traceback',
        aliases=['tb'],
    )
    async def error_traceback(self, ctx, n: int = None):
        """Print the traceback of error [n] from the error log"""
        await self.print_traceback(ctx, n)

    async def print_traceback(self, ctx, n):
        error_log = self.client.last_errors

        if not error_log:
            await ctx.send('Error log is empty')
            return

        if n is None:
            await ctx.send('Please specify an error index')
            await self.client.get_command('error').invoke(ctx)
            return

        if n >= len(error_log) or n < 0:
            await ctx.send('Error index does not exist')
            return

        exc, date, error_source, orig_content = error_log[n]
        delta = (datetime.utcnow() - date).total_seconds()
        hours = int(delta // 3600)
        seconds = int(delta - (hours * 3600))
        delta_str = f'{hours} hours and {seconds} seconds ago'
        tb = ''.join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        response = [f'`Error occured {delta_str}`']
        if error_source is not None:
            response.append(
                f'`Server:{error_source.guild.name} | Channel: {error_source.channel.name}`'
            )
            response.append(
                f'`User: {error_source.author.name}#{error_source.author.discriminator}`'
            )
            if isinstance(error_source, commands.Context):
                response.append(f'`Command: {error_source.invoked_with}`')
                response.append(error_source.message.jump_url)
            else:
                response.append(f'`Command: No Command`')
                response.append(error_source.jump_url)
        response.append(f'```python\n')
        num_chars = sum(len(line) for line in response)
        for line in tb.split('\n'):
            num_chars += len(line)
            response.append(line)
            if num_chars > 1900:
                response.append('```')
                await ctx.send('\n'.join(response))
                response = ['```python\n']
                num_chars = 0
        response.append('```')
        await ctx.send('\n'.join(response))
        if error_source is not None:
            e = Embed(title='Full command that caused the error:',
                      description=orig_content)
            e.set_footer(text=error_source.author.display_name,
                         icon_url=error_source.author.avatar_url)
        await ctx.send(embed=e)


def setup(client):
    client.add_cog(Management(client))
