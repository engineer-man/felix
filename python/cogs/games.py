from random import choice, seed, sample
from time import time
from discord.ext import commands
from discord import Member, Embed, Message

seed()

"""This is a cog for a discord.py bot.
It will provide a connect4 type game for everyone to play.
"""

COLUMN_EMOJI = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣')
CANCEL_EMOJI = '🚪'
BACKGROUND = '⚫'
TOKENS = ('🟡', '🔴', '🟠', '🟣', '🟤', '🔵', '⚪')
LAST_COLUMN_INDICATOR = '⬇️'
FILLER = '➖'  # ⬛
BOARD_EMOJI = (*COLUMN_EMOJI, CANCEL_EMOJI, BACKGROUND, LAST_COLUMN_INDICATOR, FILLER)


class Connect4Engine:
    MOVE_ACCEPTED = 0
    PLAYER1_WINNER = 1
    PLAYER2_WINNER = 2
    INVALID_MOVE = 3
    WRONG_PLAYER = 4
    DRAW = 5

    def __init__(self, player1, player2):
        self._player1 = player1
        self._player2 = player2
        self._state = [0] * 6 * 7

    @property
    def _next_up(self):
        return self._player1 if self._state.count(0) % 2 == 0 else self._player2

    def _play_move(self, player, column):
        # Wrong player
        if self._next_up != player:
            return self.WRONG_PLAYER

        # Invalid Column
        if not 1 <= column <= 7:
            return self.INVALID_MOVE

        # Column full
        if self._state[column - 1]:
            return self.INVALID_MOVE

        return self._apply_move(player, column)

    def _apply_move(self, player, column):
        next_empty = self._find_next_empty(column)
        self._state[next_empty] = 1 if player == self._player1 else 2
        winning_move = self._check_4_in_a_row(next_empty)
        if winning_move:
            if player == self._player1:
                return self.PLAYER1_WINNER
            else:
                return self.PLAYER2_WINNER
        else:
            if self._state.count(0) == 0:
                return self.DRAW
            else:
                return self.MOVE_ACCEPTED

    def _check_4_in_a_row(self, last_added):
        target_value = self._state[last_added]

        space_right = 6-last_added % 7
        space_left = last_added % 7
        space_down = 5 - last_added // 7
        space_up = last_added // 7
        directions = {
            1: space_right,
            -1: space_left,
            7: space_down,
            -7: space_up,
            6: min(space_down, space_left),
            -6: min(space_up, space_right),
            8: min(space_down, space_right),
            -8: min(space_up, space_left),
        }

        in_a_row = dict()
        for direction, distance in directions.items():
            distance = min(distance, 3)
            current = last_added
            while distance > 0:
                current += direction
                if self._state[current] == target_value:
                    in_a_row[abs(direction)] = in_a_row.get(abs(direction), 1) + 1
                    distance -= 1
                else:
                    break
        return any(x >= 4 for x in in_a_row.values())

    def _find_next_empty(self, column):
        current = column - 1
        while True:
            if current + 7 > 41:
                break
            if self._state[current + 7]:
                break
            current += 7
        return current


class Connect4Game(Connect4Engine):
    def __init__(self, player1: Member, player2: Member, p1_token: str, p2_token: str):
        self.player1 = player1
        self.player2 = player2
        self.tokens = (BACKGROUND, p1_token, p2_token)
        self.last_column = None
        super().__init__(player1.id, player2.id)

    def play_move(self, player, column):
        self.last_column = column
        return self._play_move(player.id, column)

    @property
    def next_up(self):
        return self.player1 if self._next_up == self.player1.id else self.player2

    @property
    def state(self):
        return self._state

    def get_embed(self, custom_footer=False):
        title = (
            f'Connect 4: {self.player1.display_name} ({self.tokens[1]}) '
            f'VS {self.player2.display_name} ({self.tokens[2]})'
        )
        c = self.last_column
        content = (FILLER*(c-1) + LAST_COLUMN_INDICATOR + (FILLER*(7-c)) + '\n') if c else ''

        for line in range(6):
            line_state = self.state[line*7:(line+1)*7]
            content += ''.join(str(self.tokens[x]) for x in line_state) + '\n'

        content += ''.join(COLUMN_EMOJI)

        e = Embed(
            title=title,
            description=content,
            color=0x2ECC71,
        )
        if custom_footer:
            e.set_footer(text=custom_footer)
        else:
            token = self.tokens[1] if self.next_up == self.player1 else self.tokens[2]
            e.set_footer(text=f'Next Up: {self.next_up.display_name} ({token})')

        return e


class Connect4(commands.Cog, name='Connect4'):
    def __init__(self, client):
        self.client = client
        self.waiting_games = dict()
        self.active_games = dict()

    async def start_invite(self, ctx):
        await ctx.message.delete()
        message = await ctx.send(
            f'{ctx.author.display_name} wants to start a game of Connect 4\n'
            f'Waiting for {ctx.author.display_name} to pick a color!'
        )
        self.waiting_games[message.id] = (message, ctx.author, None)
        for emoji in TOKENS:
            await message.add_reaction(emoji)
        await message.add_reaction(CANCEL_EMOJI)

    async def p1_token_pick(self, message, token):
        message, player1, _ = self.waiting_games[message.id]
        self.waiting_games[message.id] = (message, player1, token)
        await message.clear_reaction(token)
        content = message.content.split('\n')[0]
        await message.edit(
            content=content + f' - They have chosen {token}\nPick a color to join'
        )

    async def start_game(
        self,
        player1: Member,
        player2: Member,
        p1_token: str,
        p2_token: str,
        message: Message
    ):
        await message.clear_reactions()
        notification = await message.channel.send(
            f'Hey {player1.mention} - {player2.display_name} has joined your game!'
        )
        await message.edit(content='Loading ....')
        for emoji in COLUMN_EMOJI:
            await message.add_reaction(emoji)
        await message.add_reaction(CANCEL_EMOJI)
        game = Connect4Game(player1, player2, p1_token, p2_token)
        self.active_games[message.id] = (game, message)
        await message.edit(content=None, embed=game.get_embed())
        await notification.delete()

    async def finish_game(self, game, message, result):
        await message.clear_reactions()
        if result == game.DRAW:
            footer = 'The game was a draw!!'
        elif result == game.PLAYER1_WINNER:
            footer = f'{game.player1.display_name} has won the game'
        elif result == game.PLAYER2_WINNER:
            footer = f'{game.player2.display_name} has won the game'

        await message.edit(embed=game.get_embed(custom_footer=footer))
        del self.active_games[message.id]

    async def cancel_invite(self, message):
        await message.delete()
        del self.waiting_games[message.id]

    async def cancel_game(self, game, message, user):
        await message.clear_reactions()
        footer = f'The game has been cancelled by {user.display_name}'
        await message.edit(embed=game.get_embed(custom_footer=footer))
        del self.active_games[message.id]

    @commands.command(
        name='connect4',
        aliases=['c4'],
    )
    async def connect4(self, ctx):
        """Start a game of Connect 4"""
        await self.start_invite(ctx)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.id == self.client.user.id:
            return
        if reaction.message.id in self.waiting_games:
            message, player1, p1_token = self.waiting_games[reaction.message.id]

            if user.id == player1.id:
                emoji = reaction.emoji
                if emoji == CANCEL_EMOJI:
                    await self.cancel_invite(message)
                    return
                if emoji not in BOARD_EMOJI and isinstance(emoji, str):
                    if p1_token is None:
                        await self.p1_token_pick(message, emoji)

            elif p1_token:
                emoji = reaction.emoji
                if emoji not in BOARD_EMOJI and emoji != p1_token and isinstance(emoji, str):
                    player2 = user
                    p2_token = reaction.emoji
                    del self.waiting_games[reaction.message.id]
                    await self.start_game(player1, player2, p1_token, p2_token, message)
                    return

            await message.remove_reaction(reaction.emoji, user)

        elif reaction.message.id in self.active_games:
            game, message = self.active_games[reaction.message.id]
            if game.next_up != user or reaction.emoji not in (*COLUMN_EMOJI, CANCEL_EMOJI):
                await message.remove_reaction(reaction.emoji, user)
                return

            if reaction.emoji == CANCEL_EMOJI:
                await self.cancel_game(game, message, user)
                return

            result = game.play_move(user, COLUMN_EMOJI.index(reaction.emoji) + 1)
            if result in (game.PLAYER1_WINNER, game.PLAYER2_WINNER, game.DRAW):
                await self.finish_game(game, message, result)
            elif result == 0:
                await message.edit(embed=game.get_embed())

            await message.remove_reaction(reaction.emoji, user)


"""This is a cog for a discord.py bot.
It will add the hangman game to a bot

Commands:
    hangman             Start a game

The commands can be used by everyone
"""

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
        embed.add_field(
            name=f"You had {len(self.incorrect)} incorrect guesses:",
            value=", ".join(self.incorrect),
            inline=False
        )
        embed.set_footer(
            text=self.user_name,
            icon_url=self.user_avatar
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
        words = sample(text.split(), 200)
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


class MMGame():
    PEGS = ('_', '🔴', '🟠', '🟡', '🟢', '🔵', '🟣', '⚫', '🟤', '⚪', '⭕')
    COLORS = '_roygbplnwh'
    REFEREE_PEGS = ('🔴', '⚪')

    def __init__(self, player: Member, channel, difficulty=4, num_colors=6):
        self.player = player
        if difficulty not in (4, 5, 6):
            raise commands.CommandError('Invalid difficulty')
        if num_colors not in (6, 7, 8, 9, 10):
            raise commands.CommandError('Invalid difficulty')
        self.difficulty = difficulty
        self.num_colors = num_colors
        self.game = []
        self.referee = []
        self.solution = [
            choice(range(1, self.num_colors + 1))
            for _ in range(self.difficulty)
        ]
        self.last_guess_message = None
        self.last_game_message = None
        self.channel = channel

    def add_guess(self, guess):
        guess = guess.replace(' ', '')
        if not len(guess) == self.difficulty:
            raise commands.CommandError(
                f'Please provide {self.difficulty} colors')
        if any(x.lower() not in MMGame.COLORS[1:self.num_colors+1] for x in guess):
            raise commands.CommandError('Please provide valid colors for your current game')
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
        else:
            self.last_game_message = await ctx.send(heading + '\n```You have not made any guesses yet.\nUse: \'felix help mastermind\' to get instructions.```')
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
    async def mastermind(self, ctx, *, difficulty='easy'):
        """Start a game of mastermind [easy/hard/[difficulty] [num_colors]]"""
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

        if difficulty.lower() in ('easy', 'hard'):
            game_difficulty = 4 if difficulty.lower() == 'easy' else 5
            num_colors = 6 if difficulty.lower() == 'easy' else 7
        else:
            s = difficulty.lower().split()
            if len(s) != 2 or not all(x.isdigit() for x in s):
                await ctx.send('Valid difficulties: easy, hard')
                return False

            manual_difficulty = int(s[0])
            manual_num_colors = int(s[1])
            if not 4 <= manual_difficulty <= 6:
                await ctx.send('Invalid difficulty')
                return False
            if not 6 <= manual_num_colors <= 10:
                await ctx.send('Invalid number of colors')
                return False
            game_difficulty = manual_difficulty
            num_colors = manual_num_colors

        game = MMGame(
            ctx.author,
            ctx.channel,
            difficulty=game_difficulty,
            num_colors=num_colors,
        )
        self.active_games.append(game)
        instructions = (
            "**Welcome to Felix Mastermind** "
            f"Your goal is to guess the right combination of {game.difficulty} "
            "colors. After every guess you will be told how many colors are "
            "correct AND in the right position (red marker) and how many "
            "colors are correct but NOT in the right position (white marker)."
            "You can guess a color combination by typing your guess in this channel.\nA Guess is a combination of "
            f"{game.difficulty} color letters. Available colors:\n"
            "```\nBase Colors (1-6):\n"
            "r : 🔴 | o : 🟠 | y : 🟡 | g : 🟢 | b : 🔵 | p : 🟣\n"
            "For Harder difficulties (7-10):\n"
            "l : ⚫ | n : 🟤 | w : ⚪ | h : ⭕```\n\n"

            "You can cancel the game by typing:**q or quit**\n\n"
        )

        embed = Embed(title='Felix Mastermind',
                      description=instructions,
                      )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Make a guess for your running mastermind game"""
        # A hacky way to detect if user is typing a command
        if ' ' in message.content:
            return
        current_game = None
        for game in self.active_games:
            if game.player == message.author and game.channel == message.channel:
                current_game = game
                break
        ctx = await self.client.get_context(message)
        if not current_game:
            return False
        guess = message.content
        if guess in ('q', 'quit'):
            loser = True
            winner = False
        else:
            try:
                ctx.kwargs['guess'] = guess
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


async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(Hangman(client))
    await client.add_cog(Connect4(client))
    await client.add_cog(Mastermind(client))
