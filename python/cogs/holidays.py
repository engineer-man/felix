"""This is a cog for a discord.py bot.
It will add changing activity to a bot
"""

import asyncio
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks
from discord import Activity


# dict's keys are months and days combined (month|day)
HOLIDAY_DICT = {
    "0101": "watching a new year emerge",
    "0317": "playing in a pub 🇮🇪",
    "0704": "watching fireworks 🇺🇸",
    "1003": "watching people being united 🇩🇪",
    "1225": "listening Christmas carols"
}


class Holidays(commands.Cog, name='Holidays'):
    def __init__(self, client):
        self.client = client
        # Seconds till midnight from the time __init__ was called
        # +120 for a 2 minute delay
        self.seconds_till_start = round(self.get_seconds()) + 120
        self.previous_activity = None
        self.after_holiday = False
        # Task which changes the bot's presence
        self.holidays.start()

    # ----------------------------------------------
    # Helper Functions
    # ----------------------------------------------
    def get_seconds(self):
        now = dt.utcnow()
        next_day = dt(now.year, now.month, now.day) + timedelta(days=1)
        return (next_day - now).total_seconds()

    async def set_holiday(self):
        now = dt.utcnow()
        holiday = HOLIDAY_DICT.get(now.strftime('%m%d'))
        if not holiday:
            if self.after_holiday:
                await self.client.change_presence(
                    activity=self.previous_activity
                )
                self.after_holiday = False
            return
        bot_activity = self.client.guilds[0].me.activity
        if bot_activity:
            if bot_activity.name not in [
                i.split(' ', 1)[1] for i in HOLIDAY_DICT.values()
            ]:
                self.previous_activity = bot_activity
        activities = ('playing', 'streaming', 'listening', 'watching')
        _type, _name = holiday.split(' ', 1)
        if _type not in activities:
            return
        _type = activities.index(_type)
        await self.client.change_presence(
            activity=Activity(name=_name, type=_type)
        )
        self.after_holiday = True

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------
    @tasks.loop(hours=24)
    async def holidays(self):
        await self.set_holiday()

    @holidays.before_loop
    async def before_holidays(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        await self.set_holiday()
        await asyncio.sleep(self.seconds_till_start)

    def cog_unload(self):
        self.holidays.cancel()


def setup(client):
    client.add_cog(Holidays(client))
