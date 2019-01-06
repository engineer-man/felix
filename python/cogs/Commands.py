"""This is a cog for a discord.py bot.
It adds 4 commands.

Commands:
    unix all                Displays a list of the most common unix commands.
    ms-dos all              Displays a list of the most common ms-dos commands.
    unix standard           Displays a list of the most standard unix commands.
    ms-dos standard         Displays a list of the most standard ms-dos commands.
    unix unique             Displays a list of the most unique unix commands.
    ms-dos unique           Displays a list of the most unique ms-dos commands.
    unix search {word}      Searches the descriptions of the unix commands based on the word provided.
    ms-dos search {word}    Searches the descriptions of the ms-dos commands based on the word provided.
    unix trans {command}    Searches the list of unix commands for the ms-dos equivalent provided.
    ms-dos trans {command}  Searches the list of ms-dos commands for the unix equivalent provided.

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
        self.list_commands = ['all', 'standard', 'unique', 'search', 'trans']
        # TODO Need to load the list of commands for each operating system.
        with open(path.join(path.dirname(__file__), 'commands.json')) as f:
            self.os_commands = json.load(f)

    def create_response(self, array):

        response = ''

        for x in range(len(array)):
            response += '[' + array[x]['name'] + ']' + ': ' + array[x]['desc'] + '\n'

        return response

    def get_commands(self, os, option):
        
        commands = []
        
        if 'all' in option:
            commands = self.os_commands[os]['standard'] + self.os_commands[os]['unique']
        elif 'standard' in option or 'unique' in option:
            commands = self.os_commands[os][option]

        return commands

    def search_commands(self, os, word):

        all_os_commands = self.os_commands[os]['standard'] + self.os_commands[os]['unique']
        commands = []

        for x in range(len(all_os_commands)):
            if word.lower() in all_os_commands[x]['desc'].lower():
                commands.append(all_os_commands[x])

        return commands



    # TODO
    # 1.Complete translate functionality

    # ----------------------------------------------
    # Function to display similar commands list for unix commands.
    # ----------------------------------------------
    @commands.command(
        name='unix',
        brief='Unix command utility program.',
        hidden=False,
    )
    async def list_all_unix_commands(self,  ctx):
        info = ctx.message.content
        user_cmd = info.split()

        commands = []

        if len(user_cmd) == 3 and (self.list_commands.index(user_cmd[2]) < 3):
            commands = self.get_commands(user_cmd[1], user_cmd[2])
        elif len(user_cmd) == 4 and (self.list_commands.index(user_cmd[2]) == 3):
            commands = self.search_commands(user_cmd[1], user_cmd[3])

        if len(commands) > 0:
            response = self.create_response(commands)
            await ctx.send('```css\n' + response + '\n```')


    # ----------------------------------------------
    # Function to display similar commands list for ms-dos commands.
    # ----------------------------------------------
    @commands.command(
        name='ms-dos',
        brief='Ms-dos command utility program.',
        hidden=False,
    )
    async def list_all_ms_dos_commands(self, ctx):
        info = ctx.message.content
        user_cmd = info.split()

        commands = []

        if len(user_cmd) == 3 and (self.list_commands.index(user_cmd[2]) < 3):
            commands = self.get_commands(user_cmd[1], user_cmd[2])
        elif len(user_cmd) == 4 and (self.list_commands.index(user_cmd[2]) == 3):
            commands = self.search_commands(user_cmd[1], user_cmd[3])

        if len(commands) > 0:
            response = self.create_response(commands)
            await ctx.send('```css\n' + response + '\n```')


def setup(client):
    client.add_cog(Commands(client))
