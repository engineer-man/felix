"""This is a cog for a discord.py bot.
It will provide a connect4 type game for everyone to play.
"""

from discord.ext import commands
from discord import Member, Embed, Message

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


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Connect4(client))
