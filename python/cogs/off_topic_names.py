import difflib
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

from discord import Colour, Embed
from discord.ext.commands import Cog, group, check
from discord.utils import sleep_until

from .utils.converters import OffTopicName
from .utils.pagination import LinePaginator

PATH = Path("resources", "off_topic_names.txt")
EMOJIS = {
    1: "1\u20e3",
    2: "2\u20e3",
    3: "3\u20e3",
    4: "4\u20e3",
    5: "5\u20e3",
    6: "6\u20e3",
    7: "7\u20e3"
}

# Global variable for storing poll message for ot channel names
poll_id = None


def is_hero():
    async def predicate(ctx):
        return ctx.bot.user_is_hero(ctx.author)

    return check(predicate)


async def update_names(client, channel_id) -> None:
    """Background updater task that performs the daily channel name update."""
    while True:
        today_at_midnight = datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=0)
        await sleep_until(today_at_midnight + timedelta(days=1))

        channel = client.get_channel(channel_id)
        with PATH.open(encoding="utf8") as f:
            result = [n for n in f.read().splitlines()]

        poll_choices = {}
        embed = Embed(
            title="Choose the next Off Topic Name!",
            description=""
        )
        for index, name in enumerate(random.sample(result, k=7), start=1):
            embed.description += f"{EMOJIS[index]} - `#ot-{name}`\n"
            poll_choices[index] = name

        poll_msg = await channel.send(embed=embed)
        global poll_id
        poll_id = str(poll_msg.id)

        for react_emoji in EMOJIS.values():
            await poll_msg.add_reaction(react_emoji)

        await sleep_until(datetime.utcnow() + timedelta(minutes=10))
        poll_msg_updated = await channel.fetch_message(poll_id)

        top_vote = 0
        top_emoji_index = 1
        for index, reaction in enumerate(poll_msg_updated.reactions, start=1):
            if int(reaction.count) > top_vote:
                top_vote = int(reaction.count)
                top_emoji_index = index

        channel_name = poll_choices[top_emoji_index]
        await channel.edit(name=f'ot-{channel_name}')


def sub_clyde(username):
    """
    Discord disallows "clyde" anywhere in the username for webhooks. It will return a 400.
    Return None only if `username` is None.
    """

    def replace_e(match: re.Match) -> str:
        char = "е" if match[2] == "e" else "Е"
        return match[1] + char

    if username:
        return re.sub(r"(clyd)(e)", replace_e, username, flags=re.I)
    else:
        return username


class OffTopicNames(Cog):
    """Commands related to managing the off-topic category channel names."""

    def __init__(self, client):
        self.client = client
        self.updater_task = None

        self.client.loop.create_task(self.init_off_topic_updater())

    async def init_off_topic_updater(self) -> None:
        """Start off-topic channel updating event loop if it hasn't already started."""
        if self.updater_task is None:
            coro = update_names(self.client, self.client.config['ooftopic_channel'])
            self.updater_task = self.client.loop.create_task(coro)

    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        msg = reaction.message
        message_id = str(msg.id)
        if user.bot:
            return
        if message_id == poll_id:
            if reaction.emoji not in EMOJIS.values():
                await msg.remove_reaction(reaction, user)
            else:
                for r in msg.reactions:
                    async for u in r.users():
                        if not u.id == user.id:
                            continue
                        if r.emoji == reaction.emoji:
                            continue
                        await msg.remove_reaction(r, user)

    @group(
        name='otname',
        aliases=('otn',),
        invoke_without_command=True
    )
    async def otname_group(self, ctx) -> None:
        """Commands related to managing the off-topic category channel names."""
        await ctx.send_help(ctx.command)

    @is_hero()
    @otname_group.command(name='add', aliases=('a',), hidden=True)
    async def add_command(self, ctx, *, name: OffTopicName) -> None:
        """
        Adds a new off-topic name to the rotation.
        The name is not added if it is too similar to an existing name.
        """
        with PATH.open(encoding="utf8") as f:
            existing_names = [n for n in f.read().splitlines()]
        close_match = difflib.get_close_matches(str(name), existing_names, n=1, cutoff=0.8)

        if close_match:
            await ctx.send(
                f":x: The channel name `{name}` is too similar to `{close_match[0]}` (not added). "
                "Use `felix otn forceadd` to override this check."
            )
            return
        await self._add_name(ctx, str(name))

    @is_hero()
    @otname_group.command(name='forceadd', aliases=('fa',), hidden=True)
    async def force_add_command(self, ctx, *, name: OffTopicName) -> None:
        """Forcefully adds a new off-topic name to the rotation."""
        await self._add_name(ctx, str(name))

    @staticmethod
    async def _add_name(ctx, name: str) -> None:
        """Adds an off-topic channel name to the site storage."""
        with PATH.open("a+", encoding="utf8") as f:
            f.write(f"{name}\n")

        await ctx.send(f":ok_hand: Added `{name}` to the names list.")

    @is_hero()
    @otname_group.command(name='delete', aliases=('remove', 'rm', 'del'), hidden=True)
    async def delete_command(self, ctx, *, name: OffTopicName) -> None:
        """Removes a off-topic name from the list."""
        f = open(PATH, "r")
        lines = f.readlines()
        f.close()

        with PATH.open("w", encoding="utf8") as f:
            for line in lines:
                if all([line.strip() != f"{name}"]):
                    f.write(line)

        await ctx.send(f":ok_hand: Removed `{name}` from the list.")

    @otname_group.command(name='list', aliases=('l', 'ls'))
    async def list_command(self, ctx) -> None:
        """
        Lists all currently known off-topic channel names in a paginator.
        """
        with PATH.open(encoding="utf8") as f:
            result = [n for n in f.read().splitlines()]

        embed = Embed(
            title=f"Known off-topic names (`{len(result)}` total)",
            colour=Colour.blue()
        )
        if result:
            await LinePaginator.paginate(
                sorted(f"• {name}" for name in result),
                ctx, embed, max_size=100, empty=False
            )
            return
        embed.description = "Nothing here \U0001f626."
        await ctx.send(embed=embed)

    @otname_group.command(name='search', aliases=('s',))
    async def search_command(self, ctx, *, query: OffTopicName) -> None:
        """Search for an off-topic name."""
        query = OffTopicName.translate_name(str(query), from_unicode=False).lower()

        with PATH.open(encoding="utf8") as f:
            existing_names = [n for n in f.read().splitlines()]

        map_names = {
            OffTopicName.translate_name(name, from_unicode=False).lower(): name
            for name in existing_names
        }

        in_matches = {name for name in map_names.keys() if query in name}
        close_matches = difflib.get_close_matches(query, map_names.keys(), n=10, cutoff=0.70)

        lines = sorted(f"• {map_names[name]}" for name in in_matches.union(close_matches))
        embed = Embed(
            title="Query results",
            colour=Colour.blue()
        )

        if lines:
            await LinePaginator.paginate(lines, ctx, embed, max_size=400, empty=False)
            return

        embed.description = "Nothing found."
        await ctx.send(embed=embed)

    @is_hero()
    @otname_group.command(name='set', hidden=True)
    async def set_command(self, ctx, *, name: OffTopicName = None) -> None:
        """Updates the ot channel name to a random name."""
        with PATH.open(encoding="utf8") as f:
            result = [n for n in f.read().splitlines()]

        channel = self.client.get_channel(self.client.config['ooftopic_channel'])
        name = name or random.choice(result)
        await channel.edit(name=f'ot-{name}')

        if name not in result:
            await self._add_name(ctx, str(name))

        await ctx.send(f":ok_hand: ot channel name set to `#ot-{name}`.")

    @otname_group.command(name='suggest')
    async def suggest_command(self, ctx, *, name: OffTopicName) -> None:
        """Suggest a Off Topic Channel Name."""
        webhook = await self.client.fetch_webhook(self.client.config["otname_suggestion_webhook"])
        embed = Embed(
            description=f"**Suggestion:** {name}\n"
        )
        await webhook.send(
            embed=embed,
            username=sub_clyde(ctx.author.name),
            avatar_url=ctx.author.avatar_url,
            wait=True,
        )


def setup(client) -> None:
    """Load the OffTopicNames cog."""
    client.add_cog(OffTopicNames(client))
