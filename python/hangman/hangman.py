import random as rand
import os
import json
import numpy as np

words = open('./dict.txt').read().split()
hangmanval = {}
playerdata = {}

ERRORNOGAME = -1
ERRORGAMECOMP = -2
ERRORINVALID = -3
ERRORDUP = -4
LOSTGAME = -5
GAMEACTIVE = -6
WONGAME = 1
NOERROR = 0

def hangman(sid, channel):
    if not sid in playerdata:
        playerdata[sid] = {}
        savedata(playerdata, sid)
    global hangmanval
    gameid = "%s%s" % (sid, channel)

    if gameid in hangmanval:
        if "active" in hangmanval[gameid]:
            if hangmanval[gameid]["active"]:
                return GAMEACTIVE


    hangmanval[gameid] = {}
    hangmanval[gameid]["word"] = rand.choice(words).lower()
    hangmanval[gameid]["guess"] = ("\_ " * len(hangmanval[gameid]["word"])).split(" ")
    hangmanval[gameid]["guessesw"] = ""
    hangmanval[gameid]["guessesr"] = ""
    hangmanval[gameid]["letterval"] = 100 / len(hangmanval[gameid]["word"])
    hangmanval[gameid]["tries"] = 6
    hangmanval[gameid]["potpoints"] = hangmanval[gameid]["letterval"] * (len(hangmanval[gameid]["word"]) + 5)
    hangmanval[gameid]["active"] = True
    print(hangmanval[gameid]["word"])

    return hangmanval[gameid]["guess"]

def getGuess(sid, channel):
    gameid = "%s%s" % (sid, channel)
    return hangmanval[gameid]["guess"]

def getWord(sid, channel):
    gameid = "%s%s" % (sid, channel)
    return hangmanval[gameid]["word"]

def getRightLetters(sid, channel):
    gameid = "%s%s" % (sid, channel)
    return hangmanval[gameid]["guessesr"]

def getWrongLetters(sid, channel):
    gameid = "%s%s" % (sid, channel)
    return hangmanval[gameid]["guessesw"]

def getTries(sid, channel):
    gameid = "%s%s" % (sid, channel)
    return hangmanval[gameid]["tries"]

def getPotPoints(sid, channel):
    gameid = "%s%s" % (sid, channel)
    return hangmanval[gameid]["potpoints"]

def play(sid, channel, letter, uid):
    global hangmanval
    gameid = "%s%s" % (sid, channel)
    if not uid in playerdata[sid]:
        playerdata[sid][uid] = 0

    if not gameid in hangmanval:
        return ERRORNOGAME
    if not "\\_" in hangmanval[gameid]["guess"]:
        return ERRORGAMECOMP
    if not letter.isalpha() and letter != "-":
        return ERRORINVALID
    if letter in hangmanval[gameid]["guessesw"] or letter in hangmanval[gameid]["guessesr"]:
        return ERRORDUP
    if hangmanval[gameid]["tries"] == 0:
        return LOSTGAME
    elif letter in hangmanval[gameid]["word"]:
        index = 0
        found = 0
        for i in hangmanval[gameid]["word"]:
            if i == letter:
                hangmanval[gameid]["guess"][index] = i
                playerdata[sid][uid] = playerdata[sid][uid] + hangmanval[gameid]["letterval"]
                found = 1
            index = index + 1
        if found == 1:
            hangmanval[gameid]["guessesr"] = hangmanval[gameid]["guessesr"] + " " + letter
        if not "\\_" in hangmanval[gameid]["guess"]:
            playerdata[sid][uid] = playerdata[sid][uid] + hangmanval[gameid]["letterval"] * 5
            savedata(playerdata, sid)
            hangmanval[gameid]["active"] = False
            return WONGAME
    else:
        hangmanval[gameid]["guessesw"] = hangmanval[gameid]["guessesw"] + " " + letter
        hangmanval[gameid]["tries"] = hangmanval[gameid]["tries"] - 1
        playerdata[sid][uid] = playerdata[sid][uid] - 6
        if hangmanval[gameid]["tries"] == 0:
            playerdata[sid][uid] = playerdata[sid][uid] - 18
            hangmanval[gameid]["active"] = False
            return LOSTGAME
    return NOERROR

def getdata(sid):
    return playerdata[sid]

def savedata(jsonvar, sid):
    if not os.path.exists("./hangman/data/" + sid):
        os.makedirs("./hangman/data/" + sid);
    with open("./hangman/data/" + sid + "/scores.json", "w") as f:
        json.dump(jsonvar[sid], f)

def loaddata():
    if not os.path.exists("./hangman/data/"):
        return
    for folders in os.listdir("./hangman/data/"):
        with open("./hangman/data/" + folders + "/scores.json", "r") as f:
            playerdata[folders] = json.load(f)
    #print(playerdata)

def topten(sid):
    if not sid in playerdata:
        playerdata[sid] = {}
    tten = sorted(playerdata[sid].items(), key=lambda x:x[1])
    size = len(tten)
    return tten

def myscore(sid, uid):
    if uid in playerdata[sid]:
        return playerdata[sid][uid]
    else:
        return 0
