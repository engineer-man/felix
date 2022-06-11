"""This is a cog for a discord.py bot.
It will add the hangman game to a bot

Commands:
    hangman             Start a game

The commands can be used by everyone
"""
import random
from time import time

from discord import Embed
from discord.ext import commands


# Times a player is allowed to answer incorrectly
TRIES = 6
# Minimum word length
MIN_LENGTH = 5


class HangmanGame:
    def __init__(self, word, channel, author):
        self._word = word
        self._channel = channel
        self.color = author.color or 0x2ECC71
        self.user_name = author.display_name
        self.user_avatar = author.display_avatar
        self.tries = TRIES
        self.correct = []
        self.incorrect = []
        self._is_complete = False
        self._time = time()
        self.last_bot_message = None

    @property
    def is_complete(self):
        return self._is_complete

    @property
    def started_at(self):
        return self._time

    @property
    def channel(self):
        return self._channel

    def guess(self, g):
        g = g.lower()
        if g == 'quit':
            return self.completed(won=False)
        if not g.isalpha():
            return self.invalid(alpha=False)
        if len(g) == 1:
            return self.letter(g)
        return self.word(g)

    def letter(self, l):
        if l in self.correct + self.incorrect:
            return self.invalid()
        if l in self._word:
            self.correct.append(l)
            return self.state()
        else:
            self.incorrect.append(l)
            self.tries -= 1
            if self.tries <= 0:
                return self.completed(won=False)
            return self.state()

    def word(self, w):
        if w == self._word:
            return self.completed(won=True)
        return self.completed(won=False)

    def invalid(self, alpha=True):
        if not alpha:
            description = "Words contain only alphabetic characters"
        else:
            description = "You already tried that letter"
        embed = Embed(
            title="Oops",
            description=description,
            color=self.color
        )
        return embed

    def state(self):
        puzzle = [i if i in self.correct else "_" for i in self._word]
        if not any(i == "_" for i in puzzle):
            return self.completed(won=True)
        description = (
            f"Your word is: `{' '.join(puzzle)}`\n"
            f"You have {self.tries} tries left"
        )
        embed = Embed(
            title="Felix Hangman",
            description=description,
            color=self.color
        )
        embed.set_footer(
            text=self.user_name,
            icon_url=self.user_avatar
        )
        if self.correct:
            embed.add_field(
                name="Correct:",
                value=", ".join(self.correct),
                inline=False
            )
        if self.incorrect:
            embed.add_field(
                name="Incorrect:",
                value=", ".join(self.incorrect),
                inline=False
            )
        return embed

    def completed(self, won=False):
        self._is_complete = True
        title = "Nice! You won!" if won else "Aww, you lost"
        embed = Embed(
            title=title,
            description=f"The word was: ||{self._word.title()}||",
            color=self.color
        )
        return embed


class Hangman(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.words = []
        # A dict which stores currently active games
        # Key: user_id | Value: HangmanGame instance
        self.active_games = {}

    async def get_words(self, amount=100):
        async with self.client.session.get(
            "https://raw.githubusercontent.com/dwyl/" +
            "english-words/master/words_alpha.txt"
        ) as r:
            text = await r.text()
        words = random.sample(text.split(), 200)
        return [i.strip() for i in words if len(i) >= MIN_LENGTH]

    @commands.Cog.listener()
    async def on_message(self, message):
        # A hacky way to detect if user is typing a command
        if ' ' in message.content:
            return
        _id = message.author.id
        game = self.active_games.get(_id)
        if game:
            if game.channel.id != message.channel.id:
                return
            if game.last_bot_message:
                await game.last_bot_message.delete()
                game.last_bot_message = None
            await message.delete()
            game.last_bot_message = await message.channel.send(
                embed=game.guess(message.content)
            )
            game.last_user_message = message
            if game.is_complete:
                del self.active_games[_id]

    @commands.command(
        name="hangman"
    )
    async def _hangman(self, ctx):
        """Starts a game of hangman"""
        author = ctx.author
        game = self.active_games.get(author.id)
        if game:
            if game.last_bot_message:
                await game.last_bot_message.delete()
                game.last_bot_message = None
            game.last_bot_message = await ctx.send(
                f"Your game is still going in "
                f"{game.channel.mention}. Here it is:",
                embed=game.state()
            )
            return
        if not self.words:
            self.words = await self.get_words()
        word = self.words.pop()

        new_game = HangmanGame(word, ctx.channel, author)
        current_time = time()
        # Remove old games
        for user, game in self.active_games.items():
            # The time limit is 30 minutes
            if current_time - game.started_at > 1800:
                del self.active_games[user]
        self.active_games[author.id] = new_game

        description = (
            "Thank you for playing Felix Hangman, "
            f"your word is: `{('_ '*len(word)).strip()}`\n"
            f"You have {TRIES} tries\n\n"
            "Just type the letter you'd like to guess\n"
            "You can also guess the entire word by just typing it, "
            "however you only get one chance\n\n"
            "To quit the game type `quit`\n"
            "Once you start a game it'll be restricted "
            "to the channel you started it in\n"
            "Input with spaces will be ignored (this is so you would be "
            "able to use felix)\n"
            "Good luck!"
        )
        embed = Embed(
            title="Felix Hangman",
            description=description,
            color=0x2ECC71
        )
        new_game.last_bot_message = await ctx.send(embed=embed)


async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(Hangman(client))
