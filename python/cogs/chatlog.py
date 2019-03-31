"""This is a cog for a discord.py bot.
It will log all messages the bot can see to a file

Commands:
    None

Load the cog by calling client.load_extension with the name of this python file
as an argument (without the file-type extension)
    example:    bot.load_extension('chatlog')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('my_extensions.chatlog')
"""
from discord.ext import commands
from discord import TextChannel
from datetime import datetime
from aiohttp import ClientSession
import json

with open('../config.json', 'r') as conffile:
    config = json.load(conffile)

# set up log path
LOG_FILENAME = '../logs/discord_chat.log'


class ChatLog(commands.Cog, name='Chat Log'):
    def __init__(self, client):
        self.client = client
        self.logfile = open(LOG_FILENAME, 'a', encoding='utf-8')

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            # Dont log messages of bots
            return
        if not isinstance(msg.channel, TextChannel):
            # Don't log DMs
            return
        if not msg.channel.guild.id == 473161189120147456:
            # Don't log messages on servers other than "EngineerMan"
            return
        paginator = [
            msg.created_at.isoformat(),
            str(msg.channel),
            f'{msg.author.name}#{msg.author.discriminator}',
            msg.content.replace('\n', '\\n'),
        ]
        self.logfile.write('|'.join(paginator) + '\n')
        self.logfile.flush()
        # send chat message to emkc
        headers = {
            'authorization': config['emkc_key']
        }
        data = {
            'channel': paginator[1],
            'user': paginator[2],
            'message': paginator[3],
            'timestamp': paginator[0]
        }
        async with ClientSession() as session:
            async with session.post(
                'https://emkc.org/api/internal/chats',
                headers=headers,
                data=data
            ) as response:
                s = response.status
                if not s == 200:
                    print(f'ERROR while sending chat log to EMKC. Response {s}')


def setup(client):
    client.add_cog(ChatLog(client))
