"""This is a cog for a discord.py bot.
It will add auto changing holiday activity to a bot

Commands:
    activity        set the bot's status message
"""

import asyncio
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks
from discord import Activity


#pylint: disable=E1101

# dict's keys are months and days combined (month|day)
HOLIDAY_DICT = {
    "0101": "watching a new year emerge 🥂",
    "0126": "having a bbq & beers with my aussie mates 🇦🇺",
    "0317": "playing in a pub ☘️",
    "0427": "celebrating freedom day with a braai 🇿🇦",
    "0704": "watching freedom fireworks 🎇",
    "0817": "playing it's my Birthday 🎂",
    "0911": "remembering those lost 🥀",
    "1003": "watching people being united 🍺",
    "1031": "out drinking with my skeleton buddies ☠️",
    "1109": "watching walls crumble 🧱",
    "1111": "observing those who sacrificed 🎖️",
    "1224": "watching christmas trees 🎄",
    "1225": "watching christmas trees 🎄",
    "1226": "having beers for boxing day 🥊",
    "1231": "watching fireworks 🎆",
}


class ActivityMgmt(commands.Cog, name='Activity Management'):
    def __init__(self, client):
        self.client = client
        self.previous_activity = None
        self.holidays_task.start()

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    # ----------------------------------------------
    # Helper Functions
    # ----------------------------------------------
    async def check_holiday(self):
        holiday = HOLIDAY_DICT.get(dt.utcnow().strftime('%m%d'))

        if not holiday:
            if self.previous_activity:
                await self.set_activity(activity=self.previous_activity)
                self.previous_activity = None
            return

        bot_activity = self.client.main_guild.me.activity
        if bot_activity:
            if not self.previous_activity:
                self.previous_activity = bot_activity

        await self.set_activity(text=holiday)

    async def set_activity(self, *args, text=None, activity=None):
        if activity:
            await self.client.change_presence(
                activity=activity
            )
            return

        if text == '':
            await self.client.change_presence(activity=None)
            return

        activities = ('playing', 'streaming', 'listening', 'watching')
        text_split = text.split(' ')
        _activity = text_split.pop(0).lower()
        if _activity not in activities:
            return False
        _type = activities.index(_activity)
        if _type == 2 and text_split[0].lower() == 'to':
            del text_split[0]
        if _type == 1:
            _url = text_split.pop(0)
        else:
            _url = None
        _name = ' '.join(text_split)
        await self.client.change_presence(
            activity=Activity(name=_name, url=_url, type=_type)
        )
        return True

    # ----------------------------------------------
    # Command to set the bot's status message
    # ----------------------------------------------

    @commands.command(
        name='activity',
        hidden=True,
    )
    async def change_activity(self, ctx, *activity: str):
        """Set Bot activity.

        Available activities:
        \u1160playing, streaming, listening, watching.

        Example activities:
        \u1160playing [game],
        \u1160streaming [linkToStream] [game],
        \u1160listening [music],
        \u1160watching [movie]"""

        if self.previous_activity:
            await ctx.send('Sorry a holiday is in progress')
            return
        await self.set_activity(text=' '.join(activity))

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------
    @tasks.loop(hours=24)
    async def holidays_task(self):
        await self.check_holiday()

    @holidays_task.before_loop
    async def before_holidays_task(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        await self.check_holiday()
        # Seconds till midnight from now +120 for a 2 minute delay
        now = dt.utcnow()
        next_day = dt(now.year, now.month, now.day) + timedelta(days=1)
        seconds_until_midnight = (next_day - now).total_seconds() + 120
        await asyncio.sleep(seconds_until_midnight)

    def cog_unload(self):
        self.holidays_task.cancel()


def setup(client):
    client.add_cog(ActivityMgmt(client))
