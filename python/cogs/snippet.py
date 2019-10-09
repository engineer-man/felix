import json

from discord.ext import commands


class Snippet(commands.Cog, name='Snippet Upload'):

    def __init__(self, client):
        self.client = client
        self.file_extension_mapping = {
            "py": "python",
            "pyw": "python",
            "c": "c",
            "js": "javascript",
            "rs": "rust",
            "go": "go",
            "java": "java",
            "css": "css",
            "html": "html",
            "rb": "ruby",
            "yml": "yaml",
            "json": "json",
            "cpp": "cpp",
            "cs": "csharp",
            "php": "php,
            "sql": "sql",
            "xml", "xml",
            "cls": "apex",
            "tgr": "apex",
            "azcli": "azcli",
            "bat": "bat",
            "clj": "clojure",
            "coffee": "coffeescript",
            "litcoffee": "coffeescript",
            "csp": "csp",
            "Dockerfile": "dockerfile",
            "fs": "fsharp",
            "hbs": "handlebars",
            "ini": "ini",
            "less": "less",
            "lua": "lua",
            "md": "markdown",
            "msdax": "msdax",
            "mysql": "mysql",
            "m": "objective-c",
            "pl": "perl",
            "pgsql": "pgsql",
            "txt", "plaintext",
            "sats": "postiats",
            "pq": "powerquery",
            "ps": "powershell",
            "pug": "pug",
            "r": "r",
            "razor": "razor",
            "sb": "sb",
            "scm": "scheme",
            "scss": "scss",
            "sh": "shell",
            "sol": "sol",
            "st": "st",
            "swift": "swift",
            "ts": "typescript",
            "vb": "vb",
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
    @commands.command(
        name='snippet',
        aliases=['upload'],
    )
    async def snippet(self, ctx, message_id: int = None):
        """Upload attached files to EMKC Snippets.
        Include message_id to upload files from other messages
        """
        message = (ctx.message if message_id is None
                   else await ctx.fetch_message(message_id))

        # Check the message has a file
        if len(message.attachments) == 0:
            await ctx.send("Message has no attachment")
            return

        # Upload each attachment
        for attachment in message.attachments:
            filename = attachment.filename
            extension = filename.rsplit('.')[1]
            
            if filename == "Dockerfile":
                extension = "Dockerfile"

            # Check that we support the file extension
            if extension not in self.file_extension_mapping:
                await ctx.send(f"{filename} can't be uploaded, extension not recognized")
            elif attachment.size > self.size_limit:
                await ctx.send(f"{filename} is too large to be uploaded, "
                               f"the limit is {self.size_limit // 1000} kB")
            else:

                # Retrieve the contents of the file
                content = await self.download_file_contents(attachment.url)
                if content is None:
                    await ctx.send("Problem retrieving file content")
                    return

                # Upload the file to emkc and send to chat
                snippet_url = await self.upload_file(
                    self.file_extension_mapping[extension],
                    content
                )

                if snippet_url:
                    await ctx.send(f"{filename} uploaded: <{snippet_url}>")
                else:
                    await ctx.send(f"Error while uploading to EMKC")


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Snippet(client))
