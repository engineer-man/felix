"""This is a cog for a discord.py bot.
It will add some responses to a bot

Commands:
    google          make the bot post a google link
    source          make the bot post links to the engineerman github pages
    run             dummy function (is implemented in node.js part)
    gif             make felix post a random gif for a given search term
    how-to          make felix post tutorials
     ├ codeblocks       how to send discord markdown codeblocks
     └ ask              how to ask question on the server
"""

from discord.ext import commands
from discord import Embed
from datetime import datetime as dt
from urllib.parse import quote
import random
import re


class Responses(commands.Cog, name='General'):
    def __init__(self, client):
        self.client = client

    # ----------------------------------------------
    # Helper Functions
    # ----------------------------------------------
    def get_quack_string(self):
        intro = ['Ghost of duckie... Quack', 'Ghost of duckie... QUACK',
                 'Ghost of duckie... Quaaack']
        body = ['quack', 'quuuaaack', 'quack quack', 'qua...', 'quaack']
        ending = ['qua...', 'quack!', 'quack!!', 'qua..?', '..?', 'quack?',
                  '...Quack?', 'quack :slight_smile:', 'Quack??? :thinking:',
                  'QUAACK!! :angry:']
        ret = [random.choice(intro)]
        for _ in range(random.randint(1, 5)):
            ret.append(random.choice(body))
        ret.append(random.choice(3 * ending[:-1] + ending[-1:]))
        return ' '.join(ret)

    def get_year_string(self):
        now = dt.utcnow()
        year_end = dt(now.year+1, 1, 1)
        year_start = dt(now.year, 1, 1)
        year_percent = (now - year_start) / (year_end - year_start) * 100
        return f'For your information, the year is {year_percent:.1f}% over!'

    async def gif_url(self, terms):
        url = (
            f'http://api.giphy.com/v1/gifs/search' +
            f'?api_key={self.client.config["giphy_key"]}' +
            f'&q={terms}' +
            f'&limit=20' +
            f'&rating=R' +
            f'&lang=en'
        )
        async with self.client.session.get(url) as response:
            gifs = await response.json()
        if 'data' not in gifs:
            if 'message' in gifs:
                if 'Invalid authentication credentials' in gifs['message']:
                    print('ERROR: Giphy API key is not valid')
            return None
        if not gifs['data']:
            return None
        gif = random.choice(gifs['data'])['images']['original']['url']
        return gif

    # ----------------------------------------------
    # Cog Event listeners
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, msg):
        # Ignore messages sent by bots
        if msg.author.bot:
            return

        if self.client.user_is_ignored(msg.author):
            return

        if re.search(r'(?i).*quack.*', msg.content):
            await msg.channel.send(self.get_quack_string())

        if re.search(r'(?i).*what a twist.*', msg.content):
            await msg.channel.send('` - directed by M. Night Shyamalan.`')

        if re.search(
            r'(?i)(the|this) (current )?year is ' +
            r'((almost|basically) )?(over|done|finished)',
            msg.content
        ):
            await msg.channel.send(self.get_year_string())

        if re.search(
            r'(?i)send bobs and vagene',
            msg.content
        ):
            await msg.channel.send('😏 *sensible chuckle*')

        if re.search(
            r'(?i)^(hi|what\'s up|yo|hey|hello) felix',
            msg.content
        ):
            await msg.channel.send('hello')

        if re.search(
            r'(?i)^felix should i',
            msg.content
        ):
            if random.random() >= 0.5:
                response = 'the answer I am getting from my entropy is: Yes.'
            else:
                response = 'the answer I am getting from my entropy is: No.'
            await msg.channel.send(response)

        if re.search(
            r'(?i)^html is a programming language',
            msg.content
        ):
            await msg.channel.send('no it\'s not, don\'t be silly')

        if re.search(
            r'(?i)^you wanna fight, felix\?',
            msg.content
        ):
            await msg.channel.send('bring it on pal (╯°□°）╯︵ ┻━┻')

        if re.search(
            r'(?i)^arrays start at 0',
            msg.content
        ):
            await msg.channel.send('arrays definitely start at 0')

        if re.search(
            r'(?i)^arrays start at 1',
            msg.content
        ):
            await msg.channel.send('arrays do not start at 1, they start at 0')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.client.em_guild.system_channel.send(
            f'Welcome to the Engineer Man Discord Server, {member.mention}\n'
            'I\'m Felix, the server smart assistant. You can learn more about '
            'what I can do by saying `felix help`. '
            'You can view the server rules in <#484103976296644608>. '
            'Please be kind and decent to one another. '
            'Glad you\'re here!'
        )

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.command(
        name='google',
        brief='Post a google search link',
        description='Post a google search link',
        aliases=['lmgtfy'],
        hidden=False,
    )
    async def google(self, ctx, *, search_text):
        await ctx.trigger_typing()
        await ctx.send(
            f'here you go! <https://google.com/search?q={quote(search_text)}>'
        )

    @commands.command(
        name='source',
        brief='Show links to source code',
        description='Show links to engineer-man github repositories',
        aliases=['code', 'sauce', 'repo', 'repos'],
        hidden=False,
    )
    async def source(self, ctx):
        await ctx.send(
            'Youtube : <https://github.com/engineer-man/youtube-code>' +
            '\nEMKC: <https://github.com/engineer-man/emkc>' +
            '\nFelix: <https://github.com/engineer-man/felix>' +
            '\nPiston / Felix run: <https://github.com/engineer-man/piston>'
        )

    @commands.command(
        name='gif',
        brief='Post a gif',
        description='Displays a random gif for the specified search term',
        hidden=False
    )
    async def gif_embed(self, ctx, *, gif_name):
        await ctx.trigger_typing()
        gif_url = await self.gif_url(gif_name)
        if gif_url is None:
            await ctx.send(f'Sorry {ctx.author.mention}, no gif found 😔')
            # await ctx.message.add_reaction('❌')
        else:
            e = Embed(color=0x000000)
            e.set_image(url=gif_url)
            e.set_footer(text=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)

            await ctx.send(embed=e)
            # await ctx.message.add_reaction('✅')

    @commands.command(
        name='video',
        brief='Search Youtube for EM videos',
        description='Search Youtube for EM videos',
        hidden=False
    )
    async def video(self, ctx, *, term):
        video_list = []
        page_token = ''

        while True:
            url = 'https://www.googleapis.com/youtube/v3/search' +\
                '?key=' + self.client.config['yt_key'] +\
                '&channelId=UCrUL8K81R4VBzm-KOYwrcxQ' +\
                '&part=snippet,id' +\
                '&order=date' +\
                '&maxResults=50'

            if page_token:
                url += '&pageToken=' + page_token

            async with self.client.session.get(url) as response:
                videos = await response.json()

            for video in videos['items']:
                if 'youtube#video' not in video['id']['kind']:
                    continue
                video_list.append({
                    'id': video['id']['videoId'],
                    'title': video['snippet']['title']
                })

            if 'nextPageToken' not in videos:
                break

            page_token = videos['nextPageToken']

        to_send = [v for v in video_list if term.lower() in v['title'].lower()]

        if not to_send:
            response = 'Sorry, no videos found for: ' + term
        elif len(to_send) == 1:
            response = 'I found a good video: https://www.youtube.com/watch?v='\
                + to_send[0]['id']
        else:
            to_send = to_send[:5]
            response = ['I found several videos:'] +\
                ['https://www.youtube.com/watch?v=' + v['id'] for v in to_send]
            response = '\n'.join(response)

        await ctx.send(response)

    @commands.command(
        name='question',
        brief='Ask Felix a question',
        description='Ask Felix a question',
        aliases=['q'],
        hidden=False,
    )
    async def question(self, ctx, *, question):
        url = 'https://api.wolframalpha.com/v1/result?i=' + \
            f'{quote(question)}&appid={self.client.config["wolfram_key"]}'
        async with self.client.session.get(url) as response:
            answer = await response.text()
        if 'did not understand' in answer:
            answer = 'Sorry, I did not understand that'
        await ctx.send(answer)

    @commands.group(
        invoke_without_command=True,
        name='how-to',
        brief='Show useful information for newcomers',
        description='A group of commands that help newcomers',
        aliases=['howto', 'info', 'faq']
    )
    async def how_to(self, ctx):
        await self.client.help_command.command_callback(ctx, command='how-to')

    @how_to.command(
        name='codeblocks',
        brief='How to use code blocks to paste code',
        description='Instructions on how to properly paste code',
        aliases=['codeblock', 'code-blocks', 'code-block', 'code']
    )
    async def codeblocks(self, ctx):
        code_instructions = (
            "Discord has an awesome feature called **Text Markdown** which "
            "supports code with full syntax highlighting using codeblocks."
            "To use codeblocks all you need to do is properly place the "
            "backtick characters *(not single quotes)* and specify your "
            "language *(optional, but preferred)*.\n\n"
            "**This is what your message should look like:**\n"
            "*\\`\\`\\`[programming language]\nYour code here\n\\`\\`\\`*\n\n"
            "**Here's an example:**\n"
            "*\\`\\`\\`python\nprint('Hello world!')\n\\`\\`\\`*\n\n"
            "**This will result in the following:**\n"
            "```python\nprint('Hello world!')\n```\n"
            "**NOTE:** Codeblocks are also used to run code via `felix run`."
        )
        link = (
            'https://support.discordapp.com/hc/en-us/articles/'
            '210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline-'
        )

        e = Embed(title='Text markdown',
                  url=link,
                  description=code_instructions,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @how_to.command(
        name='ask',
        brief='How to properly ask a question',
        description='Instructions on how to properly ask a question',
        aliases=['questions', 'question']
    )
    async def ask(self, ctx):
        ask_instructions = (
            "From time to time you'll stumble upon a question like this:\n"
            "*Is anyone good at [this]?* / *Does anyone know [topic]?*\n"
            "Please **just ask** your question.\n\n"
            "• Make sure your question is easy to understand.\n"
            "• Use the appropriate channel to ask your question.\n"
            "• Always search before you ask (the internet is a big place).\n"
            "• Be patient (someone will eventually try to help you)."
        )

        e = Embed(title='Just ask',
                  description=ask_instructions,
                  color=0x2ECC71)
        await ctx.send(embed=e)

    @how_to.command(
        name='run',
        brief='How to properly run code with Felix',
        description='Instructions on how to properly run code with Felix',
    )
    async def run(self, ctx):
        run_instructions = (
            '**Here are my supported languages:**'
            '\npython2\npython3\njavascript\nruby\ngo\nc\ncs/csharp/c#\n'
            'c++/cpp\nr\nasm/nasm\nphp\njava\nswift\nbrainfuck/bf\nrust\n\n'
            '**You can run code by telling me things like:**\n'
            'felix run python\n'
            '\\`\\`\\`python\nyour code\n\\`\\`\\`\n'
            '**Example**:\n'
            'felix run python\n```python\nprint("test")\n```'
        )

        e = Embed(title='I can run code',
                  description=run_instructions,
                  color=0x2ECC71)
        await ctx.send(embed=e)


def setup(client):
    client.add_cog(Responses(client))
