"""This is a cog for a discord.py bot.
It will add the hangman game to a bot

    hangman             start a hangman game
    letter              guess a letter
    hichscores          show highscores of current server
    myscore             show score of player

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('hangman')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('cogs.hangman')

The commands can be used by everyone

BUG: When sending an embed with
            await ctx.send(embed=embed)
     The bot will crash without any error message.
     Crash can be avoided by also sending some text with the embed:
            await ctx.send('.', embed=embed)
"""

from discord.ext import commands
from discord import Embed
import random as rand
import os
import json


class Hangman():
    def __init__(self, client):
        self.bot = client
        with open(__file__.replace('hangman.py', 'dict.txt')) as f:
            self.words = f.read().split()
        self.hangmanval = {}
        self.playerdata = {}
        self.loaddata()
        self.ERRORNOGAME = -1
        self.ERRORGAMECOMP = -2
        self.ERRORINVALID = -3
        self.ERRORDUP = -4
        self.LOSTGAME = -5
        self.GAMEACTIVE = -6
        self.WONGAME = 1
        self.NOERROR = 0

    def hangman(self, sid, channel):
        if not sid in self.playerdata:
            self.playerdata[sid] = {}
            self.savedata(self.playerdata, sid)
        gameid = "%s%s" % (sid, channel)

        if gameid in self.hangmanval:
            if "active" in self.hangmanval[gameid]:
                if self.hangmanval[gameid]["active"]:
                    return self.GAMEACTIVE

        rand.seed()
        self.hangmanval[gameid] = {}
        self.hangmanval[gameid]["word"] = rand.choice(self.words).lower()
        self.hangmanval[gameid]["guess"] = (
            "\_ " * len(self.hangmanval[gameid]["word"])).split(" ")
        self.hangmanval[gameid]["guessesw"] = ""
        self.hangmanval[gameid]["guessesr"] = ""
        self.hangmanval[gameid]["letterval"] = 100 / \
            len(self.hangmanval[gameid]["word"])
        self.hangmanval[gameid]["tries"] = 6
        self.hangmanval[gameid]["potpoints"] = self.hangmanval[gameid]["letterval"] * \
            (len(self.hangmanval[gameid]["word"]) + 5)
        self.hangmanval[gameid]["active"] = True
        # print(self.hangmanval[gameid]["word"])

        return self.hangmanval[gameid]["guess"]

    def getGuess(self, sid, channel):
        gameid = "%s%s" % (sid, channel)
        return self.hangmanval[gameid]["guess"]

    def getWord(self, sid, channel):
        gameid = "%s%s" % (sid, channel)
        return self.hangmanval[gameid]["word"]

    def getRightLetters(self, sid, channel):
        gameid = "%s%s" % (sid, channel)
        return self.hangmanval[gameid]["guessesr"]

    def getWrongLetters(self, sid, channel):
        gameid = "%s%s" % (sid, channel)
        return self.hangmanval[gameid]["guessesw"]

    def getTries(self, sid, channel):
        gameid = "%s%s" % (sid, channel)
        return self.hangmanval[gameid]["tries"]

    def getPotPoints(self, sid, channel):
        gameid = "%s%s" % (sid, channel)
        return self.hangmanval[gameid]["potpoints"]

    def play(self, sid, channel, letter, uid):
        gameid = "%s%s" % (sid, channel)
        if not uid in self.playerdata[sid]:
            self.playerdata[sid][uid] = 0

        if not gameid in self.hangmanval:
            return self.ERRORNOGAME
        if not "\\_" in self.hangmanval[gameid]["guess"]:
            return self.ERRORGAMECOMP
        if not letter.isalpha() and letter != "-":
            return self.ERRORINVALID
        if letter in self.hangmanval[gameid]["guessesw"] or letter in self.hangmanval[gameid]["guessesr"]:
            return self.ERRORDUP
        if self.hangmanval[gameid]["tries"] == 0:
            return self.LOSTGAME
        elif letter in self.hangmanval[gameid]["word"]:
            index = 0
            found = 0
            for i in self.hangmanval[gameid]["word"]:
                if i == letter:
                    self.hangmanval[gameid]["guess"][index] = i
                    self.playerdata[sid][uid] = self.playerdata[sid][uid] + \
                        self.hangmanval[gameid]["letterval"]
                    found = 1
                index = index + 1
            if found == 1:
                self.hangmanval[gameid]["guessesr"] = self.hangmanval[gameid]["guessesr"] + " " + letter
            if not "\\_" in self.hangmanval[gameid]["guess"]:
                self.playerdata[sid][uid] = self.playerdata[sid][uid] + \
                    self.hangmanval[gameid]["letterval"] * 5
                self.savedata(self.playerdata, sid)
                self.hangmanval[gameid]["active"] = False
                return self.WONGAME
        else:
            self.hangmanval[gameid]["guessesw"] = self.hangmanval[gameid]["guessesw"] + " " + letter
            self.hangmanval[gameid]["tries"] = self.hangmanval[gameid]["tries"] - 1
            self.playerdata[sid][uid] = self.playerdata[sid][uid] - 6
            if self.hangmanval[gameid]["tries"] == 0:
                self.playerdata[sid][uid] = self.playerdata[sid][uid] - 18
                self.hangmanval[gameid]["active"] = False
                return self.LOSTGAME
        return self.NOERROR

    def getdata(self, sid):
        return self.playerdata[sid]

    def savedata(self, jsonvar, sid):
        data_path = __file__.replace('hangman.py', 'data/')
        if not os.path.exists(data_path + str(sid)):
            os.makedirs(data_path + str(sid))
        with open(data_path + str(sid) + "/scores.json", "w") as f:
            json.dump(jsonvar[sid], f)

    def loaddata(self):
        data_path = __file__.replace('hangman.py', 'data/')
        if not os.path.exists(data_path):
            return
        for folders in os.listdir(data_path):
            if folders == '.gitkeep':
                continue
            with open(data_path + folders + "/scores.json", "r") as f:
                temp = {}
                for k,v in json.load(f).items():
                    temp[int(k)] = v
                self.playerdata[int(folders)] = temp

    def topten(self, sid):
        if not sid in self.playerdata:
            self.playerdata[sid] = {}
        tten = sorted(self.playerdata[sid].items(), key=lambda x: x[1])
        return tten

    def myscore(self, sid, uid):
        if uid in self.playerdata[sid]:
            return self.playerdata[sid][uid]
        else:
            return 0

    @commands.command(name='hangman',
                      brief='Starts a game of hangman',
                      description='Starts a game of hangman')
    async def _hangman(self, ctx):
        hidden = self.hangman(ctx.message.guild.id, ctx.message.channel.name)
        if hidden == self.GAMEACTIVE:
            await ctx.send("A game is already active in this chat.")
            return
        embed = Embed(title="Duckie hangman",
                      description="Thank you for playing Duckie hang man, " +
                      "inspired by akaeddy#3508\nyour word is: " +
                      " ".join(hidden) + "\nyou have 6 mess ups\n\npotential"
                      + " points for this word: %d" % (self.getPotPoints(
                          ctx.message.guild.id, ctx.message.channel.name)),
                      color=0x801680)
        await ctx.send('.', embed=embed)

    @commands.command(name='letter',
                      brief='Guess a letter for the running game',
                      description='Guess a letter for the running game')
    async def _letter(self, ctx):
        letter = ""
        try:
            letter = ctx.message.content.split(" ")[2][0].lower()
        except Exception as e:
            await ctx.send("quaaaack quack?")
            return
        err = self.play(ctx.message.guild.id, ctx.message.channel.name, letter,
                        ctx.message.author.id)
        if err < 0:
            if err == self.LOSTGAME:
                await ctx.send("You've lost, the word was " + self.getWord(ctx.message.guild.id,
                                                                           ctx.message.channel.name))
            if err == self.ERRORNOGAME:
                await ctx.send("you need to start a game quaaaack.")
            if err == self.ERRORGAMECOMP:
                reply = "already solved; the word was " + \
                    self.getWord(ctx.message.guild.id,
                                 ctx.message.channel.name)
                await ctx.send(reply)
            if err == self.ERRORINVALID:
                await ctx.send("quaaaack quack? quack")
            if err == self.ERRORDUP:
                await ctx.send("You've already tried that letter!! Quack")
            return
        elif err == self.WONGAME:
            await ctx.send("Nice you won!!! The word was " + self.getWord(ctx.message.guild.id,
                                                                          ctx.message.channel.name))
            return

        guessesr = self.getRightLetters(
            ctx.message.guild.id, ctx.message.channel.name)
        guessesw = self.getWrongLetters(
            ctx.message.guild.id, ctx.message.channel.name)
        tries = self.getTries(ctx.message.guild.id, ctx.message.channel.name)
        guess = self.getGuess(ctx.message.guild.id, ctx.message.channel.name)

        embed = Embed(title="Duckie hangman",
                      description="your word is: " +
                      " ".join(guess) + "\nyou have "
                      + "%d" % (tries) + " mess ups\n\n"
                      + "incorrect: " + guessesw + "\n"
                      + "correct: " + guessesr,
                      color=0x801680)
        await ctx.send('.', embed=embed)

    @commands.command(name='highscores',
                      brief='Show hangman highscores',
                      description='Show hangman highscores')
    async def _highscores(self, ctx):
        names = self.topten(ctx.message.guild.id)
        embed = Embed(title="Duckie hangman",
                      description="Highscores, top ten values!",
                      color=0x161680)

        if (len(names) == 0):
            await ctx.send("There are no highscores to display")
            return

        namesdata = ""
        scoresdata = ""
        i = 1
        for n in reversed(names):
            username = ctx.message.guild.get_member(n[0])
            if username != None:
                usernamestr = "%s#%s" % (username.name, username.discriminator)
                namesdata = namesdata + ("%d) " % (i) + usernamestr) + "\n"
                scoresdata = scoresdata + "\t%d\n" % n[1]
                if i == 10:
                    break
                i = i + 1
            else:
                print("skipping: %s" % (n[0]))

        embed.add_field(name="score", value=scoresdata, inline=True)
        embed.add_field(name="users", value=namesdata, inline=True)
        await ctx.send('.', embed=embed)

    @commands.command(name='myscore',
                      brief='Show your own hangman scores',
                      description='Show your own hangman scores')
    async def _myscore(self, ctx):
        embed = Embed(
            title="Duckie hangman",
            description="your score is... " +
            "%d!" % (self.myscore(ctx.message.guild.id, ctx.message.author.id)),
            color=0x161680
        )
        await ctx.send('.', embed=embed)


def setup(client):
    client.add_cog(Hangman(client))
