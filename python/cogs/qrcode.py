"""This is a cog for a discord.py bot.
It will provide a QR Code Generator
"""

import typing
from discord.ext import commands
from .extra.qrcode.qr import generate_qr_code

class QRCode(commands.Cog, name='QRCode'):
    def __init__(self, client):
        self.client = client


    @commands.command(
        name='qr',
        aliases=['qrcode'],
    )
    async def qrcode(self, ctx, level:typing.Optional[int]=0, *, data):
        """Print a QR Code

        Error Correction levels:
        0 : L
        1 : M
        2 : Q
        3 : H
        """
        if level is None:
            level = 0
        big_str, small_str = generate_qr_code(data, level, output='all', verbose=False)
        if len(big_str) > 1990 and len(small_str) > 1990:
            raise commands.BadArgument('QR Code too big, use less data or lower error correction')
        await ctx.send('```\n' + (big_str if len(big_str) <= 1990 else small_str) + '\n```')



def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(QRCode(client))
