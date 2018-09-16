import discord
from discord.ext import commands
import asyncio
import requests
import json

TOKEN = "NDg4NzczNDQzMTczNjEzNjA4.DnjEkA.csymQPeSeEbzdqDdHAal10073fQ"
URL = "https://www.googleapis.com/youtube/v3/activities?channelId=UCrUL8K81R4VBzm-KOYwrcxQ&part=snippet&key=AIzaSyB-RN9XdC8wxojZAVIYi44gyqRuFjHMv3A"
Client = discord.Client()
client = commands.Bot(command_prefix="felix ")


# This is the Background task
async def video_check():
    global prev_id
    await client.wait_until_ready()
    # gets channel through id
    channel = client.get_channel('483977658577715222')
    # opening file to check current video title
    file = open('prev_id.txt', 'r')
    prev_id = file.read()
    file.close()
    # main loop
    while not client.is_closed:
        # check every 10 sec only
        await asyncio.sleep(10)
        # get json for latest activity of EM through youtube api
        act = (requests.get(URL)).text
        act_json = json.loads(act)
        # if the json is not empty
        if act_json["items"]:
            # check if latest activity is upload and its title is new
            if act_json["items"][0]["snippet"]["type"] == "upload" and (
            not act_json["items"][0]["snippet"]["title"] == prev_id):
                # for console
                print("New Video: " + act_json["items"][0]["snippet"]["title"])
                # send announcement
                await client.send_message(channel,
                                          "@everyone A new video has been uploaded! " + "https://www.youtube.com/watch?v=" +
                                          (act_json["items"][0]["snippet"]["thumbnails"]["high"]["url"].split("/"))[4])
                # set new title as saved title
                prev_id = act_json["items"][0]["snippet"]["title"]
                file = open('prev_id.txt', 'w')
                file.write(prev_id)
                file.close()


@client.event
async def on_ready():
    print("Ready!")


# runs background task and bot
client.loop.create_task(video_check())
client.run(TOKEN)
