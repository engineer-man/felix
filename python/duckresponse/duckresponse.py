import random

intro = ["Ghost of duckie... Quack", "Ghost of duckie... QUACK", "Ghost of duckie... Quaaack"]
body = ["quack", "quuuaaack", "quack quack", "qua...", "quaack"]
ending = [" qua...", " quack!", " quack!!", " qua..?", "..?", " quack?",
          "...Quack?", " quack :slight_smile:", " Quack??? :thinking:",
          " QUAACK!! :angry:"]
numintro = len(intro)
numbody = len(body)
numend = len(ending)

def message():
    ret = intro[random.randint(0, numintro - 1)]
    for i in range(0, random.randint(1, 5)):
        ret = ret + " " + body[random.randint(0, numbody - 1)]

    temp = random.randint(0, numend - 1)
    if temp == numend - 1:
        ret = ret + ending[random.randint(0, numend - 1)]
    else:
        ret = ret + ending[temp]
    return ret
