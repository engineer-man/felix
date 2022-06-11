"""This is a cog for a discord.py bot.
It adds Talkback
"""
from curses.ascii import isdigit
import random
from datetime import datetime as dt
from discord.ext import commands
from discord import Activity, DMChannel


class Talkback(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client
        self.last_talkback = dt.utcnow()
        self.chance = 4
        self.cooldown = 30
        random.seed()
        self.modes = {'yarr':self.get_yarr, 'australia' : self.get_australia}
        self.mode = self.get_yarr

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    @commands.group(
        invoke_without_command=True,
        name='talkback',
        hidden=True,
    )
    async def talkback(self, ctx):
        """Print current Settings"""
        await ctx.send('\n'.join([
            '```',
            'Current Settings:',
            f'Mode:     {self.mode.__name__}',
            f'Chance:   {self.chance}%',
            f'Cooldown: {self.cooldown}s',
            ' ',
            'Available modes:',
            str(list(enumerate(self.modes.keys()))),
            '```'
        ]))

    @talkback.command(
        name='mode',
        hidden=True,
    )
    async def change_mode(self, ctx, new_mode):
        """Change Talkback mode"""
        if new_mode.isnumeric():
            new_mode = int(new_mode)
            if new_mode >= len(self.modes):
                raise commands.BadArgument('Invalid mode')
            selected, self.mode = [*self.modes.items()][new_mode]
        else:
            if new_mode not in self.modes:
                raise commands.BadArgument('Invalid mode')
            selected, self.mode = new_mode, self.modes[new_mode]

        await ctx.send(f'Changed talkback mode to {selected}')


    @talkback.command(
        name='chance',
        hidden=True,
    )
    async def change_chance(self, ctx, new_chance: int):
        """Change Talkback chance"""
        if 0 < new_chance <= 100:
            self.chance = new_chance
        else:
            raise commands.BadArgument('Invalid percentage chance')
        await ctx.send(f'Changed chance to {new_chance} percent')


    @talkback.command(
        name='cooldown',
        aliases = ['cd'],
        hidden=True,
    )
    async def change_cooldown(self, ctx, new_cd: int):
        """Change Talkback cooldown"""
        if 0 < new_cd <= 1000:
            self.cooldown = new_cd
        else:
            raise commands.BadArgument('Invalid cooldown')
        await ctx.send(f'Changed cooldown to {new_cd} seconds')

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if isinstance(msg.channel, DMChannel):
            # Ignore DM
            return
        if random.randint(0, 99 // self.chance) == 0:
            if (dt.utcnow() - self.last_talkback).total_seconds() < self.cooldown:
                return
            await msg.channel.send(self.mode())
            self.last_talkback = dt.utcnow()

    def get_yarr(self):
        return random.choice([
            'Ahoy!',
            'Avast ye!',
            'Batten down the hatches!',
            'Blimey!',
            'Give no quarter!',
            'Heave ho!',
            'Landlubber!',
            'Shiver me timbers!',
            'Walk the plank!',
            'Yo ho ho!',
            'YARR!',
            'Aarrr!',
            'Weigh anchor and hoist the mizzen!',
            'Ahoy, me hearties!',
            'Cleave him to the brisket!',
            'Scurvy dog!',
            'Three sheets to the wind!',
        ])

    def get_australia(self):
        return random.choice([
            'Hey Cobber!',
            'Bangs like a dunny door at rush hour!',
            'Got a head like a cut snake!',
            'HeyHey its Saturday!',
            'Dogs breakfast',
            'Few stubbies short of a six pack',
            'Fair go mate',
            'Fair suck of the sav',
            'Dont spit the dummy!',
            'Bloody Oath',
            'What a bogan!',
            'Smashed avo on toast... questionable...',
            'Time for a cold one',
            'Out Whoop Whoop mate',
            'Watch out for the Booze Bus',
            'True Blue!',
            'Straya!',
            'No wucken furries!',
            'What a slapper!',
            'Dry as a witches tit',
            'Two Up anyone?',
            'Hey what are yous doing?',
            'Grab me a tinny cobber!',
            'You little ripper!',
            'Your statement sounds Iffy!',
            'Dont be a Gallah!',
            'Working flat out like a one armed brick layer in Baghdad!',
            'Dont be a Drongo..',
            'Throw a shrimp on the barbie..',
            'Can it wait until this arvo?',
            'Get the Brolly out',
            'Check out me new Budgie Smugglers!',
            'Stop being a Dag..',
            'Crikey, tell me more cobber!',
            'Wow.. few kangaroos short in the top paddock..'
        ])


async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(Talkback(client))
