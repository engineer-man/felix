"""This is a cog for a discord.py bot.
It will add some management commands to a bot.

Commands:
    load            load an extension / cog
    unload          unload an extension / cog
    reload          reload an extension / cog
    cogs            show currently active extensions / cogs
    activity        set the bot's status message
    version         show the hash of the latest commit
    list            make felix compute a list
        duplicates      find duplicate usernames

Events:
    on_ready        Set the bot's status to show the hash of the latest commit

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('management')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('cogs.management')

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""
from discord.ext import commands
from discord import Activity
from os import path
from discord import Activity
import requests
import subprocess
import json


class Management():
    def __init__(self, client):
        self.client = client
        with open(path.join(path.dirname(__file__), 'permissions.json')) as f:
            self.permitted_roles = json.load(f)[__name__.split('.')[-1]]

    async def __local_check(self, ctx):
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False
        return any(role in self.permitted_roles for role in user_roles)

    async def on_ready(self):
        felix_version = self.get_version_info()[0][:7]
        await self.client.change_presence(
            activity=Activity(name=f'on {felix_version}', type=0)
        )

    def get_version_info(self):
        version = 'unknown'
        date = 'unknown'
        try:
            gitlog = subprocess.check_output(
                ['git', 'log', '-n', '1', '--date=iso']).decode()
            version = gitlog.split('\n')[0].split(' ')[1]
            date = gitlog.split('\n')[2][5:].strip()
            date = date.replace(' +', 'Z+').replace(' ', 'T')
        except:
            pass
        return (version, date)

    def get_num_remote_commits(self):
        last_commit = self.get_version_info()[0]
        ext = f'?per_page=10&sha=master'
        repo = 'engineer-man/felix'
        nxt = f'https://api.github.com/repos/{repo}/commits{ext}'
        repo_data = []
        repo_shas = []
        while last_commit not in repo_shas:
            r = requests.get(nxt)
            repo_data += r.json()
            repo_shas = [x['sha'] for x in repo_data]
            try:
                nxt = r.links['next']['url']
            except:
                nxt = ''
        return (repo_shas.index(last_commit),
                repo_data[0]['commit']['author']['date'])

    # ----------------------------------------------
    # Function to disply the version
    # ----------------------------------------------
    @commands.command(name='version',
                      brief='Show latest commit hash',
                      description='Show latest commit hash',
                      hidden=True,
                      )
    async def version(self, ctx):
        version, date = self.get_version_info()
        remote_commits, remote_date = self.get_num_remote_commits()
        status = "I am up to date with 'origin/master'"
        if remote_commits:
            status = f"I am [{remote_commits}] commits behind 'origin/master'"\
                f" [{remote_date}]"
        await ctx.send(
            f'```css\nCurrent Version: [{version[:7]}].from [{date}]' +
            f'\n{status}```'
        )

    # ----------------------------------------------
    # Function to load extensions
    # ----------------------------------------------

    @commands.command(name='load',
                      brief='Load bot extension',
                      description='Load bot extension',
                      hidden=True,
                      )
    async def load_extension(self, ctx, extension_name: str):
        try:
            self.client.load_extension(extension_name)
        except Exception as e:
            await ctx.send(f'```py\n{type(e).__name__}: {str(e)}\n```')
            return
        await ctx.send(f'```css\nExtension [{extension_name}] loaded.```')

    # ----------------------------------------------
    # Function to unload extensions
    # ----------------------------------------------
    @commands.command(name='unload',
                      brief='Unload bot extension',
                      description='Unload bot extension',
                      hidden=True,
                      )
    async def unload_extension(self, ctx, extension_name: str):
        if extension_name.lower() in 'cogs.management':
            await ctx.send(f'```diff\n- Cannot unload {extension_name}```')
            return
        if self.client.extensions.get(extension_name) is None:
            return
        self.client.unload_extension(extension_name)
        await ctx.send(f'```css\nExtension [{extension_name}] unloaded.```')

    # ----------------------------------------------
    # Function to reload extensions
    # ----------------------------------------------
    @commands.command(name='reload',
                      brief='Reload bot extension',
                      description='Reload bot extension',
                      hidden=True,
                      aliases=['re']
                      )
    async def reload_extension(self, ctx, extension_name: str):
        target_extensions = [extension_name]
        if extension_name in 'all':
            target_extensions = list(self.client.extensions.keys())
        elif extension_name not in self.client.extensions:
            return
        result = []
        for ext in target_extensions:
            self.client.unload_extension(ext)
            try:
                self.client.load_extension(ext)
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
    @commands.command(name='cogs',
                      brief='Get loaded cogs',
                      description='Get loaded cogs',
                      aliases=['extensions'],
                      hidden=True,
                      )
    async def print_cogs(self, ctx):
        extensions = self.client.extensions
        response = [
            f'```css\nLoaded extensions:',
            f' {[e for e in extensions]}```'
        ]
        await ctx.send(''.join(response))
        return True

    # ----------------------------------------------
    # Function to set the bot's status message
    # ----------------------------------------------
    @commands.command(name='activity',
                      brief='Set Bot activity',
                      description='Set Bot activity.\n\n'
                      + 'Available activites:\n'
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
        brief='List stuff',
        description='Make Felix compute a list',
        hidden=True
    )
    @commands.guild_only()
    async def _list(self, ctx):
        await ctx.send('I can list stuff. Type felix help list to see what.')
        return True

    @_list.command(name='duplicates',
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


def setup(client):
    client.add_cog(Management(client))
