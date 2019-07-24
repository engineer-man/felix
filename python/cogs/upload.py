import json

from discord.ext import commands


class Upload(commands.Cog, name='Upload'):

    def __init__(self, client):
        self.client = client
        self.file_extension_mapping = {
            "py": "python",
            "c": "c",
            "js": "javascript",
            "rs": "rust",
            "go": "go",
            "java": "java",
            "css": "css",
            "html": "html",
            "rb": "ruby",
            "yml": "yaml",
        }
        self.upload_url = 'https://emkc.org/snippets'
        self.size_limit = 10_000_000  # 10 MB file limit

    async def upload_file(self, language, contents):
        payload = json.dumps({
                "language": language,
                "snip": contents,
            })

        async with self.client.session.post(self.upload_url, data=payload) as response:
            if response.status >= 400:
                return False

            response = await response.json()

            if response["status"] == "ok":
                return "https://emkc.org" + response["payload"]["url"]
            else:
                # Woops, something went wrong when sending
                return False

    async def download_file_contents(self, url):
        async with self.client.session.get(url) as response:
            if response.status == 200:
                return await response.text()

    # ----------------------------------------------
    # Cog Commands
    # ----------------------------------------------
    @commands.command(name='upload',
                      brief='Upload attached files to EMKC Snippets',
                      description='Upload attached files to EMKC Snippets. '
                                  'Include message_id to upload files from other messages')
    async def upload(self, ctx, message_id=None):
        if message_id is None:
            message_id = ctx.message.id

        message = await ctx.fetch_message(int(message_id))

        # Check the message has a file
        if len(message.attachments) == 0:
            await ctx.send("No file present")
            return

        # Upload each attachment
        for attachment in message.attachments:
            filename = attachment.filename
            extension = filename.rsplit('.')[1]

            # Check that we support the file extension
            if extension not in self.file_extension_mapping:
                await ctx.send(f"{filename} can't be uploaded, extension not recognized")
            elif attachment.size > self.size_limit:
                await ctx.send(f"{filename} is too large to be uploaded, "
                                 "the limit is {self.size_limit} bytes")
            else:

                # Retrieve the contents of the file
                content = await self.download_file_contents(attachment.url)
                if content is None:
                    await ctx.send("Problem retrieving content from Discord")
                    return

                # Upload the file to emkc and send to chat
                snippet_url = await self.upload_file(
                    self.file_extension_mapping[extension], 
                    content
                )

                if snippet_url:
                    await ctx.send(f"{filename} uploaded: {snippet_url}")
                else:
                    await ctx.send(f"Error when uploading to EMKC")


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Upload(client))
