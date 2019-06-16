"""This is a cog for a discord.py bot.
It will add some management commands to a bot.

Commands:
    embed           make the bot post an embed for you
    version         show the hash of the latest commit
    load            load an extension / cog
    unload          unload an extension / cog
    reload          reload an extension / cog
    cogs            show currently active extensions / cogs
    activity        set the bot's status message
    list            make felix compute a list
     └duplicates        find duplicate usernames

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""
import subprocess
import json
import traceback
from datetime import datetime
from discord import Activity, Embed, Member
from os import path, listdir
from discord.ext import commands


class Management(commands.Cog, name='Management'):
    def __init__(self, client):
        self.client = client
        self.reload_config()
        self.reload_permissions()

    async def cog_check(self, ctx):
        return self.client.user_has_permission(ctx.author, 'management')

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
            'what I can do by saying `felix help`. '
            'You can view the server rules in <#484103976296644608>. '
            'Please be kind and decent to one another. '
            'Glad you\'re here!'
        )

    # ----------------------------------------------
    # Error handler
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.author.send(error)
            await ctx.message.delete()
            print(f'{ctx.command} on cooldown for {ctx.author}')
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
                f'`felix help {ctx.command.name}`'
            )
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
        if isinstance(error, commands.CheckFailure):
            print(
                f'MISSING PERMISSION | USER: {ctx.author} ' +
                f'| COMMAND: {ctx.command}'
            )
            return
        print(f'Ignoring exception in command {ctx.command}:')
        traceback.print_exception(
            type(error), error, error.__traceback__
        )

    def reload_config(self):
        with open("../config.json") as conffile:
            self.client.config = json.load(conffile)

    def reload_permissions(self):
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            self.client.permissions = json.load(f)

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
                    date = date.replace(' +', 'Z+').replace(' ', 'T')
                else:
                    pass
        except Exception as e:
            print(e)
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
    # Function to disply an embed
    # ----------------------------------------------
    @commands.command(
        name='embed',
        brief='Create a text embed',
        description='Create a text embed | usage: felix embed Title|Text',
        hidden=True,
    )
    async def embed(self, ctx, *, embed_message):
        title, text = embed_message.split('|')
        embed = Embed(
            title=title,
            description=text
        )
        embed.set_footer(
            text=ctx.author.display_name,
            icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

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
        if '.' not in extension_name:
            extension_name = 'cogs.' + extension_name
        try:
            self.client.load_extension(extension_name)
        except Exception as e:
            await ctx.send(f'```py\n{type(e).__name__}: {str(e)}\n```')
            return
        await ctx.send(f'```css\nExtension [{extension_name}] loaded.```')

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
        if '.' not in extension_name:
            extension_name = 'cogs.' + extension_name
        if extension_name.lower() in 'cogs.management':
            await ctx.send(
                f"```diff\n- {extension_name} can't be unloaded" +
                f"\n+ try felix reload {extension_name}!```"
            )
            return
        if self.client.extensions.get(extension_name) is None:
            return
        self.client.unload_extension(extension_name)
        await ctx.send(f'```css\nExtension [{extension_name}] unloaded.```')

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
        if extension_name in 'all':
            target_extensions = [__name__] + \
                [x for x in self.client.extensions.keys() if not x == __name__]
        else:
            if '.' not in extension_name:
                extension_name = 'cogs.' + extension_name
            if extension_name not in self.client.extensions:
                return
            target_extensions = [extension_name]
        result = []
        for ext in target_extensions:
            try:
                self.client.reload_extension(ext)
                result.append(f'Extension [{ext}] reloaded.')
            except Exception as e:
                await ctx.send(f'```py\n{ext}:{type(e).__name__}:{str(e)}\n```')
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
    # Function to set the bot's status message
    # ----------------------------------------------
    @commands.command(
        name='activity',
        brief='Set Bot activity',
        description='Set Bot activity.\n\n'
        + 'Available activities:\n'
        + '  playing, streaming, listening, watching.\n\n'
        + 'Example activities:\n'
        + '    playing [game],\n'
        + '    streaming [linkToStream] [game],\n'
        + '    listening [music],\n'
        + '    watching [movie]',
        hidden=True,
    )
    async def change_activity(self, ctx, *activity: str):
        if not activity:
            await self.client.change_presence(activity=None)
            return
        activities = ['playing', 'streaming', 'listening', 'watching']
        text_split = ' '.join(activity).split(' ')
        _activity = text_split.pop(0).lower()
        if _activity not in activities:
            return False
        _type = activities.index(_activity)
        if _type == 1:
            _url = text_split.pop(0)
        else:
            _url = None
        _name = ' '.join(text_split)
        await self.client.change_presence(
            activity=Activity(name=_name, url=_url, type=_type)
        )
        return True

    # ----------------------------------------------
    # Function Group to clear channel of messages
    # ----------------------------------------------
    @commands.group(
        invoke_without_command=True,
        name='list',
        hidden=True
    )
    @commands.guild_only()
    async def _list(self, ctx):
        """List stuff"""
        await ctx.send_help('list')
        return True

    @_list.command(
        name='duplicates',
        brief='List duplicate usernames',
        description='List duplicate usernames')
    @commands.guild_only()
    async def duplicates(self, ctx):
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

    # ----------------------------------------------
    # Function to get the date a member joined
    # ----------------------------------------------
    @commands.command(
        name='joined',
        hidden=True,
    )
    async def joined(self, ctx, members: commands.Greedy[Member]):
        """Print the date a member joined"""
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

    # ----------------------------------------------
    # Function to pull the latest changes from github
    # ----------------------------------------------
    @commands.command(
        name='pull',
        hidden=True,
    )
    async def pull(self, ctx):
        """Pull the latest changes from github"""
        await ctx.trigger_typing()
        if not self.client.is_superuser(ctx.author):
            raise commands.CheckFailure(f'{ctx.author} is not a superuser')
        try:
            output = subprocess.check_output(
                ['git', 'pull']).decode()
            await ctx.send('```git\n' + output + '\n```')
        except Exception as e:
            await ctx.send(str(e))


def setup(client):
    client.add_cog(Management(client))
