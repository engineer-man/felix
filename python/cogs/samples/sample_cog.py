"""This is a cog for a discord.py bot.
SAMPLE

Load the cog by calling client.load_extension with the name of this python file
as an argument (without .py)
    example:    bot.load_extension('example')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('folder.example')

"""

from discord.ext import commands
from discord import Member
import asyncio


class COG_CLASS_NAME(commands.Cog,
                     name='COG_DISPLAY_NAME',
                     command_attrs=dict(hidden=False)): # Hide Cog in help
    def __init__(self, client):
        self.client = client
        self.my_task = self.client.loop.create_task(self.TASK())

    async def __local_check(self, ctx):
        """This check will automatically be applied to each command contained
        in this cog.
        Use it to decide who can use the commands in this cog.
        If this returns False, the user calling the command (ctx.message.author)
        can not use the command and will not see the command in the bot help.
        In the current state, the check will only return True if the bot owner
        executed a command
        """
        if await ctx.bot.is_owner(ctx.author):
            return True
        # Put checks here

    # ----------------------------------------------
    # Cog Event listeners
    # ----------------------------------------------
    async def on_message(self, msg):
        """This event is called every time the bot sees a new message.
        This event does not replace the bot's normal on_message event.
        It runs and in parallel to the nomal on_message event and
        all other on_message events contained in other cogs.
        """
        print(msg.content)
        # put stuff here

    # Some useful events are
    # on_connect()
    # on_ready() # Careful - this will not fire if cog is (re)loaded at run time
    # on_typing(channel, user, when)
    # on_message(message)
    # on_message_delete(message)
    # on_message_edit(msg_before, msg_after)
    # on_reaction_add(reaction, user)
    # on_reaction_remove(reaction, user)
    # on_reaction_clear(message, reactions)
    # https://discordpy.readthedocs.io/en/rewrite/api.html#event-reference

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.command(
        name='example',  # if this is omitted the function name will be used
        brief='brief description',  # shown when users execute "help"
        description='description',  # shown when users execute "help example"
        aliases=['name2', 'name3'],  # alternative ways to execute the command
        hidden=False,  # Hide the command in the bot help
    )
    # More checks possible here - examples:
    # @commands.guild_only() Command cannot be used in private messages.
    # @commands.is_owner() Command can only be used by the bot owner.
    # @commands.is_nsfw() Command can only be used in NSFW channels
    async def COMMAND_NAME(self, ctx, member: Member):
        await ctx.send(f'Hey {member.mention}, how are you?')

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------

    async def TASK(self):
        """Coroutine that can be registered as a task by calling
        self.client.loop.create_task(self.TASK())
        Important:  Do not register the task inside the on_ready() event.
                    If you reload this cog or don't load it in on startup the
                    on_ready() event will not fire.
        """
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        try:
            while not self.client.is_closed():
                print('Running Task')
                await asyncio.sleep(120)
        except asyncio.CancelledError:
            pass

    def __unload(self):
        """This Method is called when a cog is unloaded via unload_extension
        This is useful to cancel tasks that were created inside the cog"""
        self.my_task.cancel()


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(COG_CLASS_NAME(client))


def teardown(client):
    """This is called when the cog is unloaded via unload_extension"""
    pass
