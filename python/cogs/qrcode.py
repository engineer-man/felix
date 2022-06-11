"""This is a cog for a discord.py bot.
It will provide a QR Code Generator
"""

import typing
from discord.ext import commands
from .extra.qrcode.qr import generate_qr_code

class QRCode(commands.Cog, name='QRCode'):
    def __init__(self, client):
        self.client = client

    @commands.group(
        name='qr',
        aliases=['qrcode'],
        invoke_without_command = True
    )
    async def qrcode(self, ctx, level:typing.Optional[int]=0, *, data):
        """Print a QR Code - Character-size: auto

        Error Correction levels:
        0 : L
        1 : M
        2 : Q
        3 : H
        """
        if level is None:
            level = 0
        big_str, small_str = generate_qr_code(data, level, output='all', verbose=False)
        res = (big_str if len(big_str) <= 1990 else small_str)
        if len(res) > 1990:
            raise commands.BadArgument(
                'QR Code too big. Use less data, or lower error correction'
            )
        await ctx.send('```\n' + res + '\n```')

    @qrcode.command(
        name='big',
        aliases=['b']
    )
    async def qrbig(self, ctx, level:typing.Optional[int]=0, *, data):
        """Print a QR Code - Character-size: big

        Error Correction levels:
        0 : L
        1 : M
        2 : Q
        3 : H
        """
        if level is None:
            level = 0
        res = generate_qr_code(data, level, output='full_str', verbose=False)
        if len(res) > 1990:
            raise commands.BadArgument(
                'QR Code too big. Use less data, small output, or lower error correction'
            )
        await ctx.send('```\n' + res + '\n```')

    @qrcode.command(
        name='small',
        aliases=['s'],
    )
    async def qrsmall(self, ctx, level:typing.Optional[int]=0, *, data):
        """Print a QR Code - Character-size: small

        Error Correction levels:
        0 : L
        1 : M
        2 : Q
        3 : H
        """
        if level is None:
            level = 0
        res = generate_qr_code(data, level, output='half_str', verbose=False)
        if len(res) > 1990:
            raise commands.BadArgument(
                'QR Code too big. Use less data, or lower error correction'
            )
        await ctx.send('```\n' + res + '\n```')


async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(QRCode(client))
