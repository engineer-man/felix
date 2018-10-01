"""This is a cog for a discord.py bot.
It will add some management commands to a bot.

Commands:
    load            load an extension / cog
    unload          unload an extension / cog
    reload          reload an extension / cog
    cogs            show currently active extensions / cogs
    activity        set the bot's status message

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('management')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('cogs.management')

Only users belonging to a role that is specified in the corresponding
.allowed file can use the commands.
"""
from discord.ext import commands
from discord import Activity


class Management():
    def __init__(self, client):
        self.client = client
        # Load id's of roles that are allowed to use commands from this cog
        with open(__file__.replace('.py', '.allowed')) as f:
            # read .allowed file into list
            allow = f.read().strip().split('\n')
            # remove comments from allow list
            allow = [
                l.split('#')[0].strip() for l in allow if not l.startswith('#')
                ]
            self.command_enabled_roles = [int(id) for id in allow]

    # __local_command() is run on every command
    # Checks if a user is allowed to call the command
    async def __local_check(self, ctx):
        # Always allow bot owner
        if await ctx.bot.is_owner(ctx.author):
            return True
        try:
            user_roles = [role.id for role in ctx.message.author.roles]
        except AttributeError:
            return False

        return any(role in self.command_enabled_roles for role in user_roles)

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
        if extension_name in self.client.extensions:
            self.client.unload_extension(extension_name)
        try:
            self.client.load_extension(extension_name)
        except Exception as e:
            await ctx.send(f'```py\n{type(e).__name__}: {str(e)}\n```')
            return
        await ctx.send(f'```css\nExtension [{extension_name}] reloaded.```')

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
                      hidden = True,
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

def setup(client):
    client.add_cog(Management(client))
