"""This is a cog for a discord.py bot.
It adds australia
"""
import random
from datetime import datetime as dt
from discord.ext import commands
from discord import Activity, DMChannel


class Australia(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client
        self.last_australia = dt.utcnow()
        self.chance = 4
        self.cooldown = 30
        random.seed()

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if isinstance(msg.channel, DMChannel):
            # Ignore DM
            return
        if random.randint(1, 100 // self.chance) == 1:
            if (dt.utcnow() - self.last_australia).total_seconds() < self.cooldown:
                return
            australia = self.get_australia() + '!'
            await msg.channel.send(australia)
            await self.client.change_presence(
                activity=Activity(name=australia, type=0)
            )
            self.last_australia = dt.utcnow()

    def get_australia(self):
        australias = [
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
        ]
        return random.choice(australias)


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Australia(client))
