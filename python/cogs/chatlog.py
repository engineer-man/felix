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
from os import path
from datetime import datetime

# set up log paths
LOG_DIR = path.join(path.dirname(__file__), '../../logs/')
LOG_FILENAME = 'discord_chat.log'
# LOG_FILENAME = f'discord_{datetime.now().strftime("%Y-%m-%dT%H%M%S")}.log'


class ChatLog():
    def __init__(self, client):
        self.client = client
        self.logfile = open(LOG_DIR + LOG_FILENAME, 'a', encoding='utf-8')

    async def on_message(self, msg):
        if msg.author.bot:
            # Dont log messages of bots
            return
        ch_str = str(msg.channel)
        paginator = [
            datetime.now().isoformat(),
            'DM' if ch_str.startswith('Direct Message') else ch_str,
            f'{msg.author.name}#{msg.author.discriminator}',
            msg.content.replace('\n', '\\n'),
        ]
        self.logfile.write(':'.join(paginator) + '\n')
        self.logfile.flush()


def setup(client):
    client.add_cog(ChatLog(client))
