"""This is a cog for a discord.py bot.
It adds 4 commands.

Commands:
    unix list               Displays a list of the top used linux commands.
    dos list                Displays a list of the top used dos commands.
    unix unique             Displays the unique commands for a unix terminal.
    dos unique              Displays the unique commands for dos terminal.
    unix search {word}      Searches the descriptions of the unix terminal based on the word provided.
    dos search {word}       Searches the descriptions of the dos terminal based on the word provided.
    unix trans {command}    Searches the descriptions of the unix terminal based on the word provided.
    dos trans {command}     Searches the descriptions of the dos terminal based on the word provided.

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
        self.felix_commands = ['list', 'unique', 'search', 'trans']
        # TODO Need to load the list of commands for each operating system.
        with open(path.join(path.dirname(__file__), 'commands.json')) as f:
            self.os_commands = json.load(f)
            print()
            print(self.os_commands)
            print()

    def search(self, array, word):
        print('search')

    def create_response(self, array):
        print('create response')

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
        
        response = ''
        os = 'unix'
        second_column = ''
        length = -1

        if len(user_cmd) == 3 and user_cmd[2] in self.felix_commands[0]:
            second_column = 'standard'
            length = len(self.os_commands[os][second_column])
            for x in range(length):
                response += self.os_commands[os][second_column][x] + ': ' + self.os_commands['standard_desc'][x] + '\n'
        elif len(user_cmd) == 3 and user_cmd[2] in self.felix_commands[1]:
            second_column = 'unique'
            length = len(self.os_commands[os][second_column])            
            for x in range(length):
                response += x + ': Unique Description ' + x + '\n'
        #elif len(user_cmd) == 3 and user_cmd[2] in self.felix_commands[2]:
            #await ctx.send('```search``')
        #elif len(user_cmd) == 3 and user_cmd[2] in self.felix_commands[3]:
            #await ctx.send('```trans```')

        await ctx.send('```' + response + '```')
        
        print(user_cmd)

    # ----------------------------------------------
    # Function to display similar commands list for ms-dos commands.
    # ----------------------------------------------

    @commands.command(
        name='dos',
        brief='Dos command utility program.',
        hidden=False,
    )
    async def list_all_dos_commands(self, ctx):
        info = ctx.message.content
        user_cmd = info.split()

        response = ''
        os = 'dos'
        second_column = ''
        length = -1

        if len(user_cmd) == 3 and user_cmd[2] in self.felix_commands[0]:
            second_column = 'standard'
            length = len(self.os_commands[os][second_column])
            for x in range(length):
                response += self.os_commands[os][second_column][x] + ': ' + self.os_commands['standard_desc'][x] + '\n'
        elif len(user_cmd) == 3 and user_cmd[2] in self.felix_commands[1]:
            second_column = 'unique'
            length = len(self.os_commands[os][second_column])
            for x in range(length):
                response += x + ': Unique Description ' + x + '\n'
        #elif len(user_cmd) == 3 and user_cmd[2] in self.felix_commands[2]:
            #await ctx.send('```search```')
        #elif len(user_cmd) == 3 and user_cmd[2] in self.felix_commands[3]:
            #await ctx.send('```trans```')

        await ctx.send('```' + response + '```')

        print(user_cmd)

def setup(client):
    client.add_cog(Commands(client))
