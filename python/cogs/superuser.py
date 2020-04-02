"""This is a cog for a discord.py bot.
It will add some superuser commands to a bot.

Commands:
    pull       pull latest changes from github

Only users which are specified as a superuser in the config.json
can run commands from this cog.
"""

import re
import subprocess
from discord.ext import commands


class Superuser(commands.Cog, name='Superuser'):
    def __init__(self, client):
        self.client = client
        self.cog_re = re.compile(
            r'\s*python\/cogs\/(.+)\.py\s*\|\s*\d+\s*[+-]+'
        )

    async def cog_check(self, ctx):
        return self.client.user_is_superuser(ctx.author)

    # ----------------------------------------------
    # Command to pull the latest changes from github
    # ----------------------------------------------
    @commands.group(
        invoke_without_command=True,
        name='git',
        hidden=True,
    )
    async def git(self, ctx):
        """Commands to run git commands on the local repo"""
        await ctx.send_help('git')

    @git.command(
        name='pull',
    )
    async def pull(self, ctx):
        """Pull the latest changes from github"""
        await ctx.trigger_typing()
        try:
            output = subprocess.check_output(
                ['git', 'pull']).decode()
            await ctx.send('```git\n' + output + '\n```')
        except Exception as e:
            return await ctx.send(str(e))

        _cogs = [f'cogs.{i}' for i in self.cog_re.findall(output)]
        active_cogs = [i for i in _cogs if i in self.client.extensions]
        if active_cogs:
            for cog_name in active_cogs:
                await ctx.invoke(self.client.get_command('reload'), cog_name)

    # ----------------------------------------------
    # Command to reset the repo to a previous commit
    # ----------------------------------------------
    @git.command(
        name='reset',
    )
    async def reset(self, ctx, n: int):
        """Reset repo to HEAD~[n]"""
        if not n > 0:
            raise commands.BadArgument('Please specify n>0')
        await ctx.trigger_typing()
        try:
            output = subprocess.check_output(
                ['git', 'reset', '--hard', f'HEAD~{n}']).decode()
            await ctx.send('```git\n' + output + '\n```')
        except Exception as e:
            await ctx.send(str(e))

    # ----------------------------------------------
    # Commands to edit something concerning the bot or server
    # ----------------------------------------------

    @commands.group(
        invoke_without_command=True,
        name='edit',
        hidden=True,
    )
    async def edit(self, ctx):
        """Commands to edit the client user & server"""
        await ctx.send_help('edit')

    @edit.command(
        name='server_icon',
        aliases=['server_avatar', 'guild_icon', 'guild_avatar']
    )
    async def change_server_icon(self, ctx, pic_url=None):
        """Change the server icon to the attached picture or provided URL"""
        await ctx.trigger_typing()
        try:
            if pic_url:
                async with self.client.session.get(pic_url) as resp:
                    if resp.status != 200:
                        raise RuntimeError('Could not download file...')
                    pic_bytes = await resp.read()
            else:
                attachments = ctx.message.attachments
                if not len(attachments) == 1:
                    raise RuntimeError(
                        'Please attach the new icon or provide the URL'
                    )
                attachment = attachments[0]
                pic_bytes = await attachment.read()
            await ctx.guild.edit(icon=pic_bytes)
            await ctx.send('Success')
        except Exception as e:
            await ctx.send(str(e))

    @edit.command(
        name='bot_icon',
        aliases=['bot_avatar']
    )
    async def change_bot_icon(self, ctx, pic_url=None):
        """Change the bot icon to the attached picture or provided URL"""
        await ctx.trigger_typing()
        try:
            if pic_url:
                async with self.client.session.get(pic_url) as resp:
                    if resp.status != 200:
                        raise RuntimeError('Could not download file...')
                    pic_bytes = await resp.read()
            else:
                attachments = ctx.message.attachments
                if not len(attachments) == 1:
                    raise RuntimeError(
                        'Please attach the new icon or provide the URL'
                    )
                attachment = attachments[0]
                pic_bytes = await attachment.read()
            await self.client.user.edit(avatar=pic_bytes)
            await ctx.send('Success')
        except Exception as e:
            await ctx.send(str(e))


    @edit.command(
        name='bot_name',
    )
    async def change_bot_name(self, ctx, name):
        """Change the bot name"""
        try:
            await self.client.user.edit(username=name)
            await ctx.send('Success')
        except Exception as e:
            await ctx.send(str(e))


def setup(client):
    client.add_cog(Superuser(client))
