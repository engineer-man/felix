"""This is a cog for a discord.py bot.
it prints out either a random or specified challenge,
the guide to those challenges and some additional resources.

Commands:
    challenge
    ├ random         print a random challenge
    ├ num            print a specific challenge
    ├ guide          print the challenge guide
    └ guide_extra    print the additional resources from the challenge guide
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

# custom exceptions
class ChallengesNotFoundError(IOError):
    """Exception raised when Challenges are not loaded"""
    pass

class ChallengeNumberNotIntError(TypeError):
    """Exception raised when an int is not provided for a challenge number"""
    pass

class ChallengeNumberNotWithinRangeError(IndexError):
    """Exception raised when challenge number not within range"""
    pass

class Challenges(commands.Cog, name='Challenge'):
    def __init__(self, client):
        self.client = client
        self.load_challenges_file()
        if len(self.challenges) == 0:
            raise ChallengesNotFoundError("Challenges are not loaded!")

    def load_challenges_file(self):
        challenges_file = f'challenges.json'
        file_path = path.join(path.dirname(__file__), challenges_file)
        with open(file_path, encoding='utf8') as f:
            data = json.load(f)
            self.challenges = sorted(data["challenges"], 
                                key=lambda k: k["number"])
            self.guide = "\n".join(data["guide"])
            self.guide_extra = "\n".join(data["additional_resources"])

    def pick_random_challenge(self):
        if len(self.challenges) == 0:
            raise ChallengesNotFoundError("Challenges are not loaded!")
        return choice(self.challenges)

    def pick_exact_challenge(self, num):
        if len(self.challenges) == 0:
            raise ChallengesNotFoundError("Challenges are not loaded!")
        try:
            num = int(num)
        except ValueError:
            raise ChallengeNumberNotIntError("Please specify a number e.g. `1`")
        if num <= 0:
            exc_txt = f"Input cannot be less than `1`. The input was: `{num}`"
            raise ChallengeNumberNotWithinRangeError(exc_txt)
        max_num = len(self.challenges)
        if num > max_num:
            exc_txt = f"Input should not exceed `{max_num}`. " + \
                        f"The input was: `{num}`"
            raise ChallengeNumberNotWithinRangeError(exc_txt)
        return self.challenges[num-1]

    def format_challenge(self, challenge):
        formatted_challenge = (
            '```md' +
            f'\n# {challenge["number"]}' +
            f'\n< {challenge["description"]}' +
            (f'\n{challenge["extra"]} >' if challenge["extra"] else ' >') +
            f'\n[{challenge["difficulty"]}]({challenge["category"]})' +
            '```' +
            '\nguide: `felix challenge guide`' +
            '\nadditional resources: `felix challenge guide_extra`'
        )
        return formatted_challenge

    @commands.group(
        invoke_without_command=True,
        name='challenge',
        brief='Show awesome challenges',
        description='Prints all sorts of programming challenges and a guide',
        hidden=False,
        aliases=['chal', 'task', 'project']
    )
    @commands.guild_only()
    async def challenge(self, ctx):
        await self.client.help_command.command_callback(ctx,
                command='challenge')

    @challenge.command(
        name='random',
        brief='random challenge',
        description='this will randomly choose a challenge for you',
        aliases=['r', 'shuf'],
        hidden=False
    )
    @commands.guild_only()
    async def random(self, ctx):
        await ctx.trigger_typing()
        try:
            chal = self.pick_random_challenge()
            desc = self.format_challenge(chal)
        except ChallengesNotFoundError as exc:
            desc = str(exc)
        e = Embed(title='Challenge',
                  description=desc,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @challenge.command(
        name='num',
        brief='specific challenge',
        description='this will show you a specific challenge',
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
        except (ChallengesNotFoundError,
            ChallengeNumberNotIntError,
            ChallengeNumberNotWithinRangeError) as exc:
            desc = str(exc)
        e = Embed(title='Challenge',
                  description=desc,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @challenge.command(
        name='guide',
        brief='challenge guide',
        description='this will show you the guide for these challenges',
        hidden=False
    )
    @commands.guild_only()
    async def guide(self, ctx):
        await ctx.trigger_typing()
        e = Embed(title='Guide',
                  description=self.guide,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @challenge.command(
        name='guide_extra',
        brief='challenge guide - additional resources',
        description='this will show you some additional resources',
        hidden=False
    )
    @commands.guild_only()
    async def guide_extra(self, ctx):
        await ctx.trigger_typing()
        e = Embed(title='Guide - additional resources',
                  description=self.guide_extra,
                  color=0x2ECC71)
        await ctx.send(embed=e)

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Challenges(client))
