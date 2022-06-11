"""This is a cog for a discord.py bot.
It adds Lamp
"""
from discord.ext import commands


class Lamp(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client

    @commands.group(
        name='lamp',
        hidden=True,
        invoke_without_command=True,
    )
    async def lamp(self, ctx):
        """Commands to control the live stream integration"""
        await ctx.send_help('lamp')

    @lamp.command(
        name='off',
    )
    async def lamp_off(self, ctx):
        url = 'https://a1.tuyaus.com/api.json?appVersion=3.13.0&appRnVersion=5.18&channel=oem&sign=47e07d9cf53bbab369fc504760c8d3752f0f7c2f8a56fe8c63f28c99d7bb8e1c&platform=ONEPLUS%20A5000&requestId=7c696d1e-8579-4871-b271-71b6a3a093d5&lang=en&a=tuya.m.device.dp.publish&clientId=ekmnwp9f5pnh3trdtpgy&osSystem=9&os=Android&timeZoneId=America%2FChicago&ttid=sdk_tuya%40ekmnwp9f5pnh3trdtpgy&et=0.0.1&v=1.0&sdkVersion=3.13.0&time=1572717891'
        headers = {
            'User-Agent':'TY-UA=APP/Android/3.13.0/SDK/3.13.0',
            'Content-Type':'application/x-www-form-urlencoded',
            'Content-Length':'260',
            'Host':'a1.tuyaus.com',
            'Connection':'Keep-Alive',
            'Accept-Encoding':'gzip',
        }
        data = {
            'postData':'{"devId":"06200623b4e62d1a196d","dps":"{\\"1\\":false}","gwId":"06200623b4e62d1a196d"}',
            'deviceId':'0cbe6a9f082da9d8ad9607677542561f46adb4592222',
            'sid':'az152789n0645407g6y4cy235e9cec2811a8b93caefedeea3c2ce5a8',
        }
        async with self.client.session.post(url, headers=headers, data=data) as response:
            res = await response.json()
            print(res)
            if res['status'] == 'ok':
                await ctx.send('Success')

    @lamp.command(
        name='on',
    )
    async def lamp_on(self, ctx):
        print('on')
        url = 'https://a1.tuyaus.com/api.json?appVersion=3.13.0&appRnVersion=5.18&channel=oem&sign=a8a0a9914c77dc5d01f2826a2588bb25151a1d9b46688223b10586a3fc56a4c7&platform=ONEPLUS%20A5000&requestId=3a891769-255a-4a55-971a-551df700252f&lang=en&a=tuya.m.device.dp.publish&clientId=ekmnwp9f5pnh3trdtpgy&osSystem=9&os=Android&timeZoneId=America%2FChicago&ttid=sdk_tuya%40ekmnwp9f5pnh3trdtpgy&et=0.0.1&v=1.0&sdkVersion=3.13.0&time=1572717894'
        headers = {
            'User-Agent':'TY-UA=APP/Android/3.13.0/SDK/3.13.0',
            'Content-Type':'application/x-www-form-urlencoded',
            'Content-Length':'259',
            'Host':'a1.tuyaus.com',
            'Connection':'Keep-Alive',
            'Accept-Encoding':'gzip',
        }
        data = {
            'postData':'{"devId":"06200623b4e62d1a196d","dps":"{\\"1\\":true}","gwId":"06200623b4e62d1a196d"}',
            'deviceId':'0cbe6a9f082da9d8ad9607677542561f46adb4592222',
            'sid':'az152789n0645407g6y4cy235e9cec2811a8b93caefedeea3c2ce5a8',
        }
        print('sending')
        async with self.client.session.post(url, headers=headers, data=data) as response:
            res = await response.json()
            print(res)
            if res['status'] == 'ok':
                await ctx.send('Success')

async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(Lamp(client))
