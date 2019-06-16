"""This is a cog for a discord.py bot.
It will add the run command for everyone to use

Commands:
    run            Run code using the Piston API

"""

from discord.ext import commands
import typing


class Run(commands.Cog, name='Run'):
    def __init__(self, client):
        self.client = client
        self.languages = {
            'asm': 'nasm',
            'bf': 'brainfuck',
            'brainfuck': 'brainfuck',
            'c': 'c',
            'c#': 'csharp',
            'c++': 'cpp',
            'cpp': 'cpp',
            'cs': 'csharp',
            'csharp': 'csharp',
            'duby': 'ruby',
            'go': 'go',
            'java': 'java',
            'javascript': 'javascript',
            'js': 'javascript',
            'nasm': 'nasm',
            'node': 'javascript',
            'php': 'php',
            'php3': 'php',
            'php4': 'php',
            'php5': 'php',
            'py': 'python3',
            'py3': 'python3',
            'python': 'python3',
            'python2': 'python2',
            'python3': 'python3',
            'r': 'r',
            'rb': 'ruby',
            'ruby': 'ruby',
            'rust': 'rust',
            'sage': 'python3',
            'swift': 'swift',
            'bash': 'bash',
        }

    @commands.command()
    async def run(self, ctx, language: typing.Optional[str] = None):
        """Run some code
        Type "felix run" for instructions"""
        await ctx.trigger_typing()
        if not language:
            await self.client.get_command('howto run').invoke(ctx)
            return
        language = language.replace('```', '')
        if language not in self.languages:
            raise commands.BadArgument(f'Unsupported language: {language}')
        language = self.languages[language]
        message = ctx.message.content.split('```')
        if len(message) < 3:
            raise commands.BadArgument('No code or invalid code present')
        source = message[1]
        source = source[source.find('\n'):].strip()

        url = 'https://emkc.org/api/internal/piston/execute'
        headers = {'Authorization': self.client.config["emkc_key"]}
        data = {'language': language, 'source': source}

        async with self.client.session.post(
            url,
            headers=headers,
            data=data
        ) as response:
            r = await response.json()
        if not r or 'status' not in r:
            await ctx.send('Sorry, invalid response from Piston server')
            return
        if r['status'] not in 'ok' or r['payload']['output'] is None:
            await ctx.send('Sorry, execution problem')
            return
        await ctx.send(
            f'Here is your output {ctx.author.mention}\n'
            + '```\n'
            + '\n'.join(r['payload']['output'].split('\n')[:30])
            + '```'
        )


def setup(client):
    client.add_cog(Run(client))
