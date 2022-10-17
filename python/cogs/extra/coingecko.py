"""This is a cog for a discord.py bot.
it collects current crypto prices from coingecko simple api

Commands:
    coin
    ├ price         full name of token eg. bitcoin for multiple leave a space
    ├ value         current market price for token
    ├ graph         price graph for token(s)
    ├ tokens        WIP > list of all tokens on coingeko
    └ currencies    all conversion possible currencies for comparisons (default USD)
"""

import asyncio

from datetime import datetime as dt

import pandas as pd
import matplotlib.pyplot as plt

from discord.ext import commands, tasks
from discord import Embed, File


class Coingecko(commands.Cog, name='Coin'):
    """Custom wrapper around the official CoinGecko API:
    Docs: https://www.coingecko.com/en/api/documentation"""
    API_URL_BASE = 'https://api.coingecko.com/api/v3'
    CG_ICON = 'https://cdn.discordapp.com/attachments/788621973709127693/988362901213548604/cg.webp'

    def __init__(self, client, currency='usd', api_base=API_URL_BASE, cg_icon=CG_ICON):
        self.client = client
        self.currency = currency
        self.api_base = api_base
        self.cg_icon = cg_icon
        self.currencies = []
        self.tokens = []
        self.base_url = 'https://www.coingecko.com/'

        self.supported_currencies.start()  # pylint: disable=E1101
        self.supported_tokens.start()  # pylint: disable=E1101

    def get_embed(self, **kwargs):
        """generate an embed using a standard branding template"""
        embed = Embed(**kwargs)
        embed.set_thumbnail(url=self.cg_icon)
        embed.set_footer(
            text=f'Data provided by CoinGecko\n{self.base_url}',
            icon_url=self.cg_icon
        )
        return embed

    @tasks.loop(minutes=1)
    async def supported_currencies(self):
        """list of all supported currencies - list"""
        async with self.client.session.get(
            f'{self.api_base}/simple/supported_vs_currencies'
        ) as response:
            _currencies = await self.get_data_safely(ctx=None, response=response)
            if _currencies:
                # only update our list of currencies if we actually got them
                self.currencies = _currencies

    @tasks.loop(minutes=1)
    async def supported_tokens(self):
        """generate a list of supported tokens"""
        async with self.client.session.get(f'{self.api_base}/coins/list') as response:
            _tokens = await self.get_data_safely(ctx=None, response=response)
            if _tokens:
                # only update our list of tokens if we actually got them
                self.tokens = [(token['id'], token['symbol'])
                               for token in _tokens]

    # ----------------------------------------------
    # helper functions...
    # ----------------------------------------------

    def get_token(self, token_partial_name_or_symbol: str):
        """fetch a token by name or symbol and return the id"""
        _token_id = None
        for (token_id, token_symbol) in self.tokens:
            if token_partial_name_or_symbol.lower() in (token_id.lower(), token_symbol.lower()):
                _token_id = token_id
                break
        return _token_id

    async def create_tokens_graph(self, ctx, num_days: int, vs_currency: str, *tokens):
        """create a plot graph from a bunch of given tokens over a number of days"""
        labels = {'family': 'serif', 'color': 'black', 'size': 15}
        headings = {'family': 'serif', 'color': 'darkred', 'size': 20}

        if len(tokens) == 1:
            plt.title(self.get_token(tokens[0]).title(), fontdict=headings)
        else:
            plt.title('Multiple Tokens', fontdict=headings)

        plt.figure(figsize=[12.8, 9.6])
        plt.xlabel(f'Last {num_days} Days', fontdict=labels)
        plt.ylabel(f'Price {vs_currency.upper()}', fontdict=labels)
        plt.grid(axis='y')

        for token in tokens:
            ticker = token.upper()
            token = self.get_token(token)

            async with self.client.session.get(
                f'{self.api_base}/coins/{token}/market_chart?vs_currency={vs_currency}' +
                f'&days={num_days}&interval=daily'
            ) as response:
                data = await self.get_data_safely(ctx, response)
                if not data:
                    # return because there might have been an error with the API
                    return
            _df = pd.DataFrame(data['prices'])
            _df['dt'] = pd.to_datetime((_df[0] // 1000), unit='s')
            _df['pr'] = round(_df[1], 2)

            plt.plot(_df['dt'], _df['pr'], label=f'{ticker} - {token.title()}')
            plt.tick_params(axis='x', rotation=25)
            plt.legend()

        plt.savefig('tokens_graph.png')
        plt.cla()
        return True

    # ----------------------------------------------
    # coingecko simple api cog commands
    # ----------------------------------------------

    @commands.group(
        pass_context=True,
        name='coingecko',
        aliases=['cg'],
        hidden=True,
        invoke_without_command=True,
    )
    async def coin(self, ctx):
        """Commands to view current token prices"""
        await ctx.send_help('coingecko')

    @coin.command(
        name='ping',
        hidden=True
    )
    async def coingecko_ping(self, ctx):
        """ping the coingecko server to check the latency"""
        start = dt.utcnow()
        async with self.client.session.get(f'{self.api_base}/ping') as response:
            data = await self.get_data_safely(ctx, response)
            stop = dt.utcnow()
            if not data:
                # return because there might have been an error with the API
                return
            time_diff = stop - start
            mills = round(time_diff.total_seconds() * 1_000)
            await ctx.send(embed=self.get_embed(
                title=list(data.keys())[0].replace('_', ' ').title(),
                description=f'{list(data.values())[0]} :rocket:'
                f'\n\n:ping_pong: took {mills}ms\n',
                color=0xFFFF00
            ))

    @coin.command(
        name='price',
        aliases=['$']
    )
    async def token_price(self, ctx, *token):
        """Current price for {token} or {token1} {token2} {token3}"""

        if not self.tokens:
            return await ctx.send(embed=self.get_embed(
                color=0xFF0000,
                title='API error while fetching data',
                description='Unable to fetch tokens from API, please try again later'
            ))
        tokens = ','.join((str(self.get_token(x)) for x in token))

        async with self.client.session.get(
            f'{self.api_base}/simple/price?ids={tokens}&vs_currencies={self.currency}'
            '&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true'
        ) as response:
            data = await self.get_data_safely(ctx, response)
            if not data:
                # return because there might have been an error with the API
                return
            for token, prices in data.items():
                embed = self.get_embed(
                    title=f'{token.title()} Price',
                    url=f'{self.base_url}en/coins/{token}',
                    color=0xFFFF00
                )
                for desc, value in prices.items():
                    match desc:
                        case 'usd':
                            value = round(value, 2)
                            embed.add_field(
                                name='Price (USD)',
                                value=f'${value:,}',
                                inline=True
                            )
                        case 'usd_market_cap':
                            value = int(round(value, 0))
                            embed.add_field(
                                name='Market Cap (USD)',
                                value=f'{value:,}',
                                inline=True
                            )
                        case 'usd_24h_vol':
                            value = int(round(value, 0))
                            embed.add_field(
                                name='24hr Volume (USD)',
                                value=f'{value:,}',
                                inline=True
                            )
                        case 'usd_24h_change':
                            value = round(value, 2)
                            embed.add_field(
                                name='24hr Change (USD)',
                                value=f'{value:,}%',
                                inline=True
                            )
                await ctx.send(embed=embed)
                await asyncio.sleep(1)

    @coin.command(
        name='value',
        aliases=['val', 'howmuch']
    )
    async def token_amount(self, ctx, token: str, currency: str, amt: float = None):
        """Current value for X amount of tokens. {token} {currency} {amount}"""
        if not self.tokens:
            return await ctx.send(embed=self.get_embed(
                color=0xFF0000,
                title='API error while fetching data',
                description='Unable to fetch tokens from API, please try again later'
            ))
        if not self.currencies:
            return await ctx.send(embed=self.get_embed(
                color=0xFF0000,
                title='API error while fetching data',
                description='Unable to fetch supported currencies from API, please try again later'
            ))
        token_err = token
        token = self.get_token(token.lower())

        if not token:
            return await ctx.send(embed=self.get_embed(
                color=0xFF0000,
                title='User input error',
                description=f'Token: `{token_err}` invalid or not found!'
            ))

        async with self.client.session.get(
            f'{self.api_base}/simple/price?ids={token}&vs_currencies={currency}'
        ) as response:
            data = await self.get_data_safely(ctx, response)
            if not data:
                return

            if currency not in self.currencies:
                return await ctx.send(embed=self.get_embed(
                    color=0xFF0000,
                    title='User input error',
                    description=f'{currency.upper()} not found, supported currencies:\n'
                    f'```{", ".join(self.currencies)}```'
                ))

            if not amt:
                return await ctx.send(embed=self.get_embed(
                    color=0xFFFF00,
                    title='User input error',
                    description=f'Amount `{amt}` not a valid amount.'
                ))

            embed = self.get_embed(
                color=0xFFFF00,
                title=f'{token.title()} Price',
                url=f'{self.base_url}/en/coins/{token}'
            )
            embed.add_field(
                name='Token Amt',
                value=amt,
                inline=True
            )
            embed.add_field(
                name=f'Price ({currency.upper()})',
                value=f'${data[token][currency] * amt:,}',
                inline=True
            )
        await ctx.send(embed=embed)

    @coin.command(
        name='graph',
        aliases=['g', 'chart']
    )
    async def token_graph(self, ctx, num_days: int, vs_currency: str, *tokens):
        """Price graph for token(s), {num_days} {vs_currency} {token1} {token2} {token3}..."""
        if not self.tokens:
            return await ctx.send(embed=self.get_embed(
                color=0xFF0000,
                title='API error while fetching data',
                description='Unable to fetch tokens from API, please try again later'
            ))
        if not self.currencies:
            return await ctx.send(embed=self.get_embed(
                color=0xFF0000,
                title='API error while fetching data',
                description='Unable to fetch supported currencies from API, please try again later'
            ))
        for token in tokens:
            token_err = token

            if not self.get_token(token):
                return await ctx.send(embed=self.get_embed(
                    color=0xFF0000,
                    title='User input error',
                    description=f'Token: `{token_err}` invalid or not found!'
                ))

        if vs_currency not in self.currencies:
            return await ctx.send(embed=self.get_embed(
                color=0xFFFF00,
                title='User input error',
                description=f'{vs_currency.upper()} not found, supported currencies:\n'
                            f'```{", ".join(self.currencies)}```'
            ))

        await ctx.typing()

        if await self.create_tokens_graph(ctx, num_days, vs_currency, *tokens):
            img_name = 'tokens_graph.png'
            with open(img_name, 'rb') as token_graph:
                file = File(token_graph, filename=img_name)
                embed = self.get_embed(
                    title='Token graph')
                embed.set_image(url=f'attachment://{img_name}')
                await ctx.send(file=file, embed=embed)

    async def get_data_safely(self, ctx, response):
        """Fetch the json data from the response or return a user friendly message from the API"""
        data = await response.json()
        if response.status == 200:
            return data
        msg = 'Unable to process response from CoinGecko API' \
            f'\n{response.status} - {response.reason}'
        if
        # do we have context so we can inform the user?
        if ctx:
            await ctx.send(embed=self.get_embed(
                title='API error while fetching data',
                description=f'{msg}, please try again later',
                color=0xFF0000
            ))
        else:
            # let's just log it so the local admin can see what's happening
            print(
                f'{msg}, {response = }')   # pylint: disable=W0212

    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------


async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(Coingecko(client))
