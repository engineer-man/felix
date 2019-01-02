"""This is a cog for a discord.py bot.
It adds 4 commands.

Commands:
    cmdlist         Displays a list of the top used linux commands and their ms-dos counterparts.
    cmdunique       Displays the unique commands for a particular operating system.
                    - Must provide an operating system parameter such as mac, unix, ubuntu, windows 
    cmdsearch       Searches the descriptions of both operating systems list to provide a useful command to the user.
                    - Must provide a searching parameter
    cmdtrans        Translates the command from one operating system to the other
                    - Must provide operating system to search and the command

The purpose of this cog is to show users the different versions of the same command 
between operating systems and the uniqueness that comes with each as well.

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('poll')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('my_extensions.poll')

"""

from discord.ext import commands
from os import path
import re
import json

class Commands():
    def __init__(self, client):
        self.client = client

        # TODO Need to load the list of commands for each operating system.
        #with open(path.join(path.dirname(__file__), 'commands.json')) as f:
        #    self.permitted_roles = json.load(f)[__name__.split('.')[-1]]


    # ----------------------------------------------
    # Function to display similar commands list for both unix and ms-dos commands.
    # ----------------------------------------------

    @commands.command(
        name='cmdlist',
        brief='Gets a list of unix and ms-dos commands',
        hidden=False,
    )
    async def list_all_commands(self, ctx):
        info = ctx.message.content
        print(info)

    # ----------------------------------------------
    # Function to display unique commands based on the operating system.
    # ----------------------------------------------

    @commands.command(
        name='cmdunique',
        brief='Displays unique commands based on the operating system provided',
        description='felix cmdunique [operating_system]',
        hidden=False,
    )
    async def list_unique_commands(self, ctx):
        info = ctx.message.content
        print(info)

    # ----------------------------------------------
    # Function to display the commands unique to the search parameters provided.
    # ----------------------------------------------

    @commands.command(
        name='cmdsearch',
        brief='Displays unique commands based on the operating system and word',
        description='felix cmdsearch [operating_system] [search_word]',
        hidden=False,
    )
    async def list_search_commands(self, ctx):
        info = ctx.message.content
        print(info)

    # ----------------------------------------------
    # Function to display the command for the other operating system's command.
    # ----------------------------------------------

    @commands.command(
        name='cmdtrans',
        brief='Looks up the command\'s counterpart',
        description='felix cmdtrans [operating_system] [command_couterpart]',
        hidden=False,
    )
    async def list_trans_commands(self, ctx):
        info = ctx.message.content
        print(info)

def setup(client):
    client.add_cog(Commands(client))
