"""This is a cog for a discord.py bot.
It will provide a mastermind type game for everyone to play.

Commands:
    mastermind [easy/hard]      Start a game
    mastermind guess            Make a guess on a running mastermind game
    mastermind quit             Quit a running game
Short Commands:
    mastermind -> mm
    mastermind guess -> mm g
"""

from random import choice, seed
from discord.ext import commands
from discord import Member, Embed

seed()


class MMGame():
    PEGS = ('_', '💖', '🧡', '💛', '💚', '💙', '💜', '🖤')
    COLORS = '_roygbpl'
    REFEREE_PEGS = ('🔴', '⚪')

    def __init__(self, player: Member, difficulty=4):
        self.player = player
        if difficulty not in (4, 5):
            raise commands.CommandError('Invalid difficulty')
        self.difficulty = difficulty
        self.game = []
        self.referee = []
        self.solution = [
            choice(range(1, 7 if self.difficulty == 4 else 8))
            for _ in range(self.difficulty)
        ]
        self.last_guess_message = None
        self.last_game_message = None

    def add_guess(self, guess):
        guess = guess.replace(' ', '')
        if not len(guess) == self.difficulty:
            raise commands.CommandError(
                f'Please provide {self.difficulty} colors')
        if any(x.lower() not in MMGame.COLORS for x in guess):
            raise commands.CommandError('Please provide valid colors')
        self.game.append([MMGame.COLORS.index(x) for x in guess.lower()])
        return True

    def update_referee(self):
        if not len(self.game) == len(self.referee) + 1:
            return False
        solution = self.solution.copy()
        guess = self.game[-1].copy()
        correct = 0
        for x in range(self.difficulty):
            if guess[x] == solution[x]:
                correct += 1
                guess[x] = 0
                solution[x] = 0
        almost_correct = 0
        for x in range(self.difficulty):
            candidate = guess[x]
            if not candidate:
                continue
            if candidate in solution:
                almost_correct += 1
                solution[solution.index(candidate)] = 0
        self.referee.append([correct, almost_correct])

    async def process_game(self, ctx):
        self.add_guess(ctx.kwargs['guess'])
        self.update_referee()
        loser = True if len(self.game) == 12 else False
        winner = True if self.referee[-1][0] == self.difficulty else False
        if self.last_guess_message:
            await self.last_guess_message.delete()
        self.last_guess_message = ctx.message
        await self.print_to_ctx(ctx)
        return (loser, winner)

    async def print_to_ctx(self, ctx, heading=''):
        game_to_print = []
        for row, referee in zip(self.game, self.referee):
            row_str = ''
            for peg in row:
                row_str += MMGame.PEGS[peg]
            row_str += '|'
            row_str += MMGame.REFEREE_PEGS[0] * referee[0]
            row_str += MMGame.REFEREE_PEGS[1] * referee[1]
            game_to_print.append(row_str)
        to_send = []
        for n, line in enumerate(game_to_print, start=1):
            to_send.append(str(n).rjust(2) + ': ' + line)
        to_send = '```\n' + '\n'.join(to_send) + '```' if to_send else ''
        if self.last_game_message:
            await self.last_game_message.delete()
        if to_send:
            self.last_game_message = await ctx.send(heading + '\n' + to_send)
        return True

    def get_solution(self):
        solution_str = ''
        for peg in self.solution:
            solution_str += MMGame.PEGS[peg]
        return solution_str


class Mastermind(commands.Cog, name='Mastermind'):
    def __init__(self, client):
        self.client = client
        self.active_games = []

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.group(
        name='mastermind',
        aliases=['mm'],
        invoke_without_command=True,
    )
    async def mastermind(self, ctx, difficulty='easy'):
        """Start a game of mastermind [easy/hard]"""
        current_game = None
        for game in self.active_games:
            if game.player == ctx.author:
                current_game = game
                break
        if current_game:
            await current_game.print_to_ctx(
                ctx,
                'You already have an active game - here it is:'
            )
            return False
        if difficulty.lower() not in ('easy', 'hard'):
            await ctx.send('Valid difficulties: easy, hard')
            return False

        game = MMGame(ctx.author, 4 if difficulty.lower() == 'easy' else 5)
        self.active_games.append(game)
        instructions = (
            "**Welcome to Felix Mastermind** "
            f"Your goal is to guess the right combination of {game.difficulty} "
            "colors. After every guess you will be told how many colors are "
            "correct AND in the right position (red marker) and how many "
            "colors are correct but NOT in the right position (white marker)."
            "You can guess a color combination by typing \n**felix mastermind "
            "guess xxx** \nwhere xxx should be replaced by a combination of "
            f"{game.difficulty} color letters. Available colors:\n"
            "r : RED\n"
            "o : ORANGE\n"
            "y : YELLOW\n"
            "g : GREEN\n"
            "b : BLUE\n"
            "p : PURPLE\n"
            "l : BLACK (only for hard difficulty)\n\n"

            "You can cancel the game with:\n**felix mastermind quit**\n\n"
            "Shortcuts:\nfelix mastermind - **felix mm**\n"
            "felix mastermind guess - **felix mm g**"
        )

        embed = Embed(title='Felix Mastermind',
                      description=instructions,
                      )
        await ctx.send(embed=embed)

    @mastermind.command(
        name='guess',
        aliases=['g'],
    )
    async def guess(self, ctx, *, guess):
        """Make a guess for your running mastermind game"""
        current_game = None
        for game in self.active_games:
            if game.player == ctx.author:
                current_game = game
                break
        if not current_game:
            await ctx.send('Cannot find active game')
            return False
        try:
            loser, winner = await current_game.process_game(ctx)
        except commands.CommandError as e:
            await ctx.send(e)
            return False
        if winner or loser:
            to_send = 'The Game is Over - '
            to_send += 'you win' if winner else (
                'you lose\nSolution:' + '`' + current_game.get_solution() + '`'
            )
            self.active_games.remove(current_game)
            await ctx.send(to_send)

    @mastermind.command(
        name='quit',
        aliases=['q'],
    )
    async def quit(self, ctx):
        """Quit your running mastermind game"""
        current_game = None
        for game in self.active_games:
            if game.player == ctx.author:
                current_game = game
                break
        if not current_game:
            await ctx.send('Cannot find active game')
            return False
        self.active_games.remove(current_game)
        await ctx.send('Game Cancelled')


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Mastermind(client))
