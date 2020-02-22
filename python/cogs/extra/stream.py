"""This is a cog for a discord.py bot.
It provides a youtube livestream chat question integration with discord
"""

import asyncio
import json
from datetime import datetime
from urllib.parse import quote
import googleapiclient.discovery
from google_auth_oauthlib import flow as googleFlow
from discord import Embed, File
from discord.ext import tasks, commands

#pylint: disable=E1101


class Stream(commands.Cog, name='Stream'):
    def __init__(self, client):
        self.client = client
        self.LIVE_CHAT_ID = None
        self.staging_ch = None
        self.questions_ch = None
        self.donations_ch = None
        self.PREFIXES = ['q ', 'question ', 'q:', 'question:']
        self.staged_questions = dict()
        self.forwarded_questions = dict()
        self.reaction_in_progress = set()
        self.youtube_api = None
        self.check_date = datetime(2000, 1, 1)

    async def cog_check(self, ctx):
        return self.client.user_is_superuser(ctx.author)

    # ----------------------------------------------
    # Helper Functions
    # ----------------------------------------------
    def load_state(self):
        with open("../state.json", "r") as statefile:
            return json.load(statefile)

    def load_refresh_token(self):
        state = self.load_state()
        return state.get('refresh_token', '')

    def save_refresh_token(self, refresh_token):
        state = self.load_state()
        state['refresh_token'] = refresh_token
        with open("../state.json", "w") as statefile:
            return json.dump(state, statefile, indent=1)

    def load_stream_channels(self):
        state = self.load_state()
        return state.get('stream_channels', [])

    def save_stream_channels(self, stream_channels):
        state = self.load_state()
        state['stream_channels'] = stream_channels
        with open("../state.json", "w") as statefile:
            return json.dump(state, statefile, indent=1)

    def set_up_api(self, credentials):
        self.youtube_api = googleapiclient.discovery.build(
            serviceName="youtube", version="v3", credentials=credentials
        )
        return True

    def refresh_api(self):
        refresh_token = self.load_refresh_token()
        if not refresh_token:
            return False
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        client_secrets_file = "../api_secrets_file"
        flow = googleFlow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes
        )
        flow.oauth2session.refresh_token(
            flow.client_config['token_uri'],
            refresh_token=refresh_token,
            client_id=flow.client_config['client_id'],
            client_secret=flow.client_config['client_secret']
        )
        credentials = flow.credentials
        self.set_up_api(credentials)
        return True

    async def stage_question(self, question_text, author_name, avatar):
        e = Embed(
            description=question_text,
            color=0x2ECC71
        )
        e.set_footer(
            text=author_name,
            icon_url=avatar,
        )
        question = await self.staging_ch.send(embed=e)
        await question.add_reaction('✅')
        await question.add_reaction('⛔')
        self.staged_questions[question.id] = question
        return True

    async def forward_question(self, question_id):
        old_question = self.staged_questions[question_id]
        e = old_question.embeds[0]
        question = await self.questions_ch.send(embed=e)
        await question.add_reaction('❌')
        self.forwarded_questions[question.id] = question
        await old_question.delete()
        self.staged_questions.pop(old_question.id)
        return True

    async def finish_question(self, question_id):
        old_question = self.forwarded_questions[question_id]
        await old_question.delete()
        self.forwarded_questions.pop(old_question.id)
        return True

    async def drop_question(self, question_id):
        old_question = self.staged_questions[question_id]
        await old_question.delete()
        self.staged_questions.pop(old_question.id)
        return True

    async def post_donation(self, message, amount, author_name, avatar):
        donation_message = f'{message}\n'
        if amount:
            donation_message += f'({amount} USD)'

        e = Embed(
            description=donation_message,
            color=0xFFED46
        )
        e.set_footer(
            text=author_name,
            icon_url=avatar,
        )
        await self.donations_ch.send(embed=e)
        return True

    # ----------------------------------------------
    # Listeners
    # ----------------------------------------------
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        emoji = reaction.emoji
        msg = reaction.message
        msg_id = msg.id
        if msg_id in self.reaction_in_progress:
            return
        self.reaction_in_progress.add(msg_id)
        if msg_id in self.staged_questions:
            if emoji == '✅':
                await self.forward_question(msg_id)
            elif emoji == '⛔':
                await self.drop_question(msg_id)
        elif msg_id in self.forwarded_questions:
            if emoji == '❌':
                await self.finish_question(msg_id)
        self.reaction_in_progress.remove(msg_id)

    # ----------------------------------------------
    # Commands
    # ----------------------------------------------
    @commands.group(
        name='stream',
        hidden=True,
        invoke_without_command=True,
    )
    async def stream(self, ctx):
        """Commands to control the live stream integration"""
        await ctx.send_help('stream')

    @stream.command(
        name='dump',
    )
    async def dump(self, ctx):
        request = self.youtube_api.liveChatMessages().list(
            liveChatId=self.LIVE_CHAT_ID,
            part="snippet,authorDetails"
        )
        response = request.execute()
        ch = self.client.get_channel(self.client.config['report_channel'])
        with open('donation.json', 'w') as temp_file:
            json.dump(response, temp_file)
        with open('donation.json', 'rb') as temp_file:
            file_to_send = File(temp_file)
            await ch.send(file=file_to_send)

    @stream.command(
        name='authenticate',
    )
    async def authenticate(self, ctx):
        """The stream owner has to run this to authenticate felix on youtube"""
        channel = ctx.channel
        caller = ctx.author
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        client_secrets_file = "../api_secrets_file"
        flow = googleFlow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes
        )
        flow.redirect_uri = flow._OOB_REDIRECT_URI
        await ctx.send(
            'Please visit ' +
            flow.authorization_url()[0] +
            ' and paste authorization code here (into your next message)'
        )
        try:
            def check(m):
                return m.author.id == caller.id and m.channel.id == channel.id
            code_msg = await self.client.wait_for(
                'message',
                check=check,
                timeout=120
            )
        except asyncio.TimeoutError:
            await channel.send(f'TIMEOUT - Authentication Cancelled')
            return
        code = code_msg.content
        flow.fetch_token(code=code)
        credentials = flow.credentials
        refresh_token = credentials.refresh_token
        self.save_refresh_token(refresh_token)
        await ctx.send('Authentication Successful - refresh token saved')

    @stream.command(
        name='setup',
    )
    async def stream_setup(self, ctx):
        """Setup the 'staging' and 'question' channel"""
        channel = ctx.channel
        caller = ctx.author

        def check(m):
            return m.author.id == caller.id and m.channel.id == channel.id

        try:
            await channel.send('Please specify the "Staging" channel ID')
            staging_msg = await self.client.wait_for(
                'message',
                check=check,
                timeout=60
            )

            await channel.send('Please specify the "Questions" channel ID')
            questions_msg = await self.client.wait_for(
                'message',
                check=check,
                timeout=60
            )

            await channel.send('Please specify the "Donations" channel ID')
            donations_msg = await self.client.wait_for(
                'message',
                check=check,
                timeout=60
            )

        except asyncio.TimeoutError:
            await channel.send(f'TIMEOUT - Setup Cancelled')
            return

        staging_id = int(staging_msg.content)
        questions_id = int(questions_msg.content)
        donations_id = int(donations_msg.content)

        stream_channels = [staging_id, questions_id, donations_id]
        self.save_stream_channels(stream_channels)
        await ctx.send('Setup Successful - question channels saved')

    @stream.command(
        name='start',
    )
    async def stream_start(self, ctx):
        """Find active stream and start monitoring the live chat"""
        try:
            self.refresh_api()
            if not self.youtube_api:
                raise RuntimeError('API failiure - are you authenticated')
        except:
            await ctx.send('Please run `felix stream authenticate` first')
            return False

        stream_channels = self.load_stream_channels()
        if not stream_channels:
            await ctx.send('Please run `felix stream setup` first')
            return False

        self.staging_ch = self.client.get_channel(stream_channels[0])
        self.questions_ch = self.client.get_channel(stream_channels[1])
        self.donations_ch = self.client.get_channel(stream_channels[2])

        request = self.youtube_api.liveBroadcasts().list(
            part="snippet",
            broadcastStatus="active",
            broadcastType="all"
        )
        response = request.execute()
        if not response['items']:
            await ctx.send('No active livestream found')
            return
        self.LIVE_CHAT_ID = response['items'][0]['snippet']['liveChatId']
        await ctx.send(
            'Found Stream: `' +
            response['items'][0]['snippet']['title'] +
            '` - Attaching to live chat'
        )
        self.read_chat_task.start()

    @stream.command(
        name='stop',
    )
    async def stream_stop(self, ctx):
        """Stop monitoring the live chat"""
        self.read_chat_task.stop()
        await ctx.send('Detached from stream Chat')

    # ----------------------------------------------
    # Tasks
    # ----------------------------------------------
    @tasks.loop(seconds=10.0)
    async def read_chat_task(self):
        request = self.youtube_api.liveChatMessages().list(
            liveChatId=self.LIVE_CHAT_ID,
            part="snippet,authorDetails"
        )
        response = request.execute()
        chat_messages = response['items']
        for msg in chat_messages:
            msg_type = msg['snippet']['type']
            if not msg_type in ('textMessageEvent', 'superChatEvent'):
                continue
            message_date_str = msg['snippet']['publishedAt']
            message_date = datetime.fromisoformat(message_date_str[:-1])
            if message_date <= self.check_date:
                continue
            self.check_date = message_date

            author_name = msg['authorDetails']['displayName']
            author_image = msg['authorDetails']['profileImageUrl']

            if msg_type == 'superChatEvent':
                amount = int(msg['snippet']['superChatDetails']['amountMicros']) / 1000000
                currency = msg['snippet']['superChatDetails']['currency']
                if not currency == 'USD':
                    question = f'{currency} {amount} in dollars'
                    url = 'https://api.wolframalpha.com/v1/result?i=' + \
                    f'{quote(question)}&appid={self.client.config["wolfram_key"]}'
                    async with self.client.session.get(url) as response:
                        answer = await response.text()
                    dollar_value = answer.split(' ')[1]
                else:
                    dollar_value = ''

                display_message = msg['snippet']['displayMessage']
                await self.post_donation(display_message, dollar_value, author_name, author_image)
                continue

            message_text = msg['snippet']['textMessageDetails']['messageText']
            prefix_len = 0
            for prefix in self.PREFIXES:
                if message_text.lower().startswith(prefix):
                    prefix_len = len(prefix)
                    break
            if not prefix_len:
                continue

            await self.stage_question(
                message_text[prefix_len:],
                author_name,
                author_image
            )
    # ----------------------------------------------

    def cog_unload(self):
        self.read_chat_task.cancel()


def setup(client):
    client.add_cog(Stream(client))
