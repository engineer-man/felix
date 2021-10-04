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

import json
from os import path
from random import choice
from discord.ext import commands
from discord import Embed

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


class ChallengeDifficultyNotFoundError(KeyError):
    """Exception raised when requested challenge difficulty does not exist"""
    pass


class Challenges(commands.Cog, name='Challenges'):
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
            self.difficulties = [x.lower() for x in data["difficulties"]]

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
            raise ChallengeNumberNotIntError(
                "Please specify a number e.g. `1`")
        if num <= 0:
            exc_txt = f"Input cannot be less than `1`. The input was: `{num}`"
            raise ChallengeNumberNotWithinRangeError(exc_txt)
        max_num = len(self.challenges)
        if num > max_num:
            exc_txt = f"Input should not exceed `{max_num}`. " + \
                f"The input was: `{num}`"
            raise ChallengeNumberNotWithinRangeError(exc_txt)
        return self.challenges[num - 1]

    def pick_difficulty_challenge(self, difficulty):
        if len(self.challenges) == 0:
            raise ChallengesNotFoundError("Challenges are not loaded!")
        difficulty = difficulty.lower()
        if difficulty not in self.difficulties:
            difficulties = ", ".join(self.difficulties)
            exc_txt = "The difficulty must be one of the following:" + \
                f"`{difficulties}`"
            raise ChallengeDifficultyNotFoundError(exc_txt)
        chosen_challenges = [
            x for x in self.challenges if
            x['difficulty'].lower() == difficulty]
        return choice(chosen_challenges)

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
        aliases=['chal', 'task', 'project']
    )
    async def challenge(self, ctx):
        """'Show awesome challenges'"""
        await ctx.send_help('challenge')

    @challenge.command(
        name='random',
        aliases=['r', 'shuf'],
    )
    async def random(self, ctx):
        """Randomly choose a challenge"""
        #await ctx.trigger_typing()
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
        aliases=['n'],
    )
    async def num(
        self, ctx,
        n: int
    ):
        """Choose a specific challenge"""
        #await ctx.trigger_typing()
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
    )
    async def guide(self, ctx):
        """Print the guide"""
        #await ctx.trigger_typing()
        e = Embed(title='Guide',
                  description=self.guide,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @challenge.command(
        name='guide_extra',
    )
    async def guide_extra(self, ctx):
        """Print the additional resources"""
        #await ctx.trigger_typing()
        e = Embed(title='Guide - additional resources',
                  description=self.guide_extra,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @challenge.command(
        name='difficulty',
        aliases=['dif', 'd'],
    )
    async def difficulty(self, ctx, difficulty: str):
        """Choose by difficulty"""
        #await ctx.trigger_typing()
        try:
            chal = self.pick_difficulty_challenge(difficulty)
            desc = self.format_challenge(chal)
        except (ChallengesNotFoundError,
                ChallengeDifficultyNotFoundError) as exc:
            desc = str(exc)
        e = Embed(title='Challenge',
                  description=desc,
                  color=0x2ECC71)
        await ctx.send(embed=e)

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Challenges(client))
