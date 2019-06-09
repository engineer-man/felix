"""This is a cog for a discord.py bot.
it prints out either a random or specified challenge

Commands:
    challenge
    ├ random     print a random challenge
    └ num        print a specific challenge

Load the cog by calling client.load_extension with the name of this python file
as an argument (without .py)
    example:    bot.load_extension('example')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('folder.example')

"""

# TODO: load users and save challenge against name
# check if user exists
# yes, check if user has been given this challenge already
#      yes, get a new challenge
#      no, send challenge to user, update file, save it
# no, send challenge to user, update file, save it


from discord.ext import commands
from discord import Embed
from random import choice
from os import path
import json

def my_sort(iterable, key_name, itemget=False):
    if itemget == False:
        return sorted(iterable, key=lambda k: k[key_name])
    else:
        from operator import itemgetter
        return sorted(iterable, key=itemgetter(key_name)) 

def obj_dict(obj):
    return obj.__dict__

class Challenge(commands.Cog, name='Challenge'):
    def __init__(self, client):
        self.client = client
        self.reload_challenges()
        if len(self.challenges) == 0:
            raise Exception(f"Challenges have not been loaded!")
        print(len(self.challenges), flush=True)

    def reload_challenges(self):
        challenges_file = f'challenges.json'
        with open(path.join(path.dirname(__file__), challenges_file), encoding='utf8') as f:
            data = json.load(f)
            self.challenges = my_sort(data["challenges"], "number", True)

    def print_challenges(self):
        if len(self.challenges) == 0:
            raise Exception(f"Challenges have not been loaded!")
        for challenge in self.challenges:
            print(challenge, flush=True)

    def pick_random_challenge(self):
        if len(self.challenges) == 0:
            raise Exception(f"Challenges have not been loaded!")
        return choice(self.challenges)

    def pick_exact_challenge(self, num):
        try:
            num = int(num)
        except:
            raise Exception(f"Please specify a number e.g. `1`")
        if num <= 0:
            raise Exception(f"Input cannot be less than {1}. The input was: {num}")
        print(num, len(self.challenges), flush=True)
        if num > len(self.challenges):
            raise Exception(f"Input should not exceed {len(self.challenges)}. The input was: {num}")
        if len(self.challenges) == 0:
            raise Exception(f"Challenges have not been loaded!")
        return self.challenges[num-1]

    def format_challenge(self, challenge):
        formatted_challenge = (
            f'• Number: {challenge["number"]}' +
            f'\n• Description: {challenge["description"]}' +
            (f'\n• Extra: {challenge["extra"]}' if challenge["extra"] else '') +
            f'\n• Difficulty: {challenge["difficulty"]}' +
            f'\n• Category: {challenge["category"]}'
        )
        return formatted_challenge

    @commands.group(
        invoke_without_command=True,
        name='challenge',
        brief='Pick a challenge',
        description='Prints details of a random or specific challenge',
        hidden=False,
        aliases=['chal', 'task', 'project']
    )
    @commands.guild_only()
    async def challenge(self, ctx):
        await self.client.help_command.command_callback(ctx, command='challenge')

    @challenge.command(
        name='random',
        brief='random challenge',
        description='this command will randomly choose a challenge for you',
        aliases=['r', 'shuf'],
        hidden=False
    )
    @commands.guild_only()
    async def random(self, ctx):
        await ctx.trigger_typing()
        try:
            chal = self.pick_random_challenge()
            desc = self.format_challenge(chal)
        except Exception as exc:
            desc = str(exc)
        e = Embed(title='Challenge',
                  description=desc,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @challenge.command(
        name='num',
        brief='specific challenge',
        description='this command will show you a specific challenge',
        aliases=['n'],
        hidden=False
    )
    @commands.guild_only()
    async def num(
        self, ctx,
        n: int
    ):
        await ctx.trigger_typing()
        try:
            chal = self.pick_exact_challenge(n)
            desc = self.format_challenge(chal)
        except Exception as exc:
            desc = str(exc)
        print(desc, flush=True)
        e = Embed(title='Challenge',
                  description=desc,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @challenge.command(
        name='reload',
        brief='reload challenges',
        description='this command will reload all challenges',
        hidden=True
    )
    @commands.guild_only()
    async def reload(
        self, ctx
    ):
        await ctx.trigger_typing()
        self.reload_challenges()
        await ctx.send("challenges reloaded")

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Challenge(client))
