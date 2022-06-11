import itertools
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import discord
from bs4 import BeautifulSoup
from discord import ChannelType
from discord.ext.commands import BadArgument, Cog, command
from discord.ext.tasks import loop

RECENT_THREADS_URL = (
    "https://mail.python.org/archives/list/{name}@python.org/recent-threads"
)
THREAD_API_URL = (
    "https://mail.python.org/archives/api/list/{name}@python.org/thread/{id}/"
)
MAILMAN_PROFILE_URL = "https://mail.python.org/archives/users/{id}/"
THREAD_URL = "https://mail.python.org/archives/list/{list}@python.org/thread/{id}/"

COLOURS = itertools.cycle((0xFFD241, 0x3775A8, 0xFFFFFE))

STATE_JSON = Path("../state.json")
STATE_KEY = "mailing_list"
STATE_MSG_HASHES_KEY = "message_id_hash"


class PythonMailingList(Cog):
    def __init__(self, client):
        self.client = client
        self.mailing_lists_names = {}
        self.python_channel = self.client.config["python_channel"]
        self.existing_messages = {}

        self.fetch_new_posts.start()

    async def cog_check(self, ctx):
        return self.client.user_is_admin(ctx.author)

    @staticmethod
    def write_mail_hash(message_id_hash):
        state_json = json.loads(STATE_JSON.read_text())
        if not state_json.get(STATE_MSG_HASHES_KEY):
            state_json[STATE_MSG_HASHES_KEY] = {}
        state_json[STATE_MSG_HASHES_KEY][message_id_hash] = datetime.now().timestamp()

        with open(STATE_JSON, "w") as statefile:
            json.dump(state_json, statefile, indent=1)

    @staticmethod
    def mail_exists(message_id_hash):
        state_json = json.loads(STATE_JSON.read_text())
        mails_sent = state_json.get(STATE_MSG_HASHES_KEY)

        if not mails_sent:
            return False
        elif message_id_hash in mails_sent:
            return True
        else:
            return False

    @command()
    async def pythonmail(self, ctx, maillist: str):
        """Subscribe to a python mailing list"""
        async with self.client.session.get(
            RECENT_THREADS_URL.format(name=maillist)
        ) as resp:
            if resp.status != 200:
                raise BadArgument(
                    message=f"'{maillist} is not a valid python mailing list name."
                )

        python_channel: discord.TextChannel = self.client.get_channel(
            self.python_channel
        )
        thread = await python_channel.create_thread(
            name=maillist,
            type=ChannelType.public_thread,
            reason=f"Creating new thread for posting {maillist} mailing list.",
        )

        state_json = json.loads(STATE_JSON.read_text())
        if not state_json.get(STATE_KEY):
            state_json[STATE_KEY] = {}

        state_json[STATE_KEY][maillist] = thread.id

        with open(STATE_JSON, "w") as statefile:
            json.dump(state_json, statefile, indent=1)

        await ctx.send(
            f"✅ Successfully added {maillist}, listening to {thread.mention}."
        )

    @loop(minutes=30)
    async def fetch_new_posts(self):
        # Clear the old message hashes from the state.json
        state_json = json.loads(STATE_JSON.read_text())
        mails_sent = state_json.get(STATE_MSG_HASHES_KEY)

        if not mails_sent:
            await self.post_maillist()
            return

        for mail_hash, timestamp in mails_sent.copy().items():
            if (datetime.now() - datetime.fromtimestamp(timestamp)) > timedelta(days=7):
                del state_json[STATE_MSG_HASHES_KEY][mail_hash]
        with open(STATE_JSON, "w") as statefile:
            json.dump(state_json, statefile, indent=1)

        await self.post_maillist()

    @fetch_new_posts.before_loop
    async def get_webhook_names_and_channel(self):
        await self.client.wait_until_ready()

        async with self.client.session.get(
            "https://mail.python.org/archives/api/lists"
        ) as resp:
            lists = await resp.json()

        for mail in lists:
            key = mail["name"].split("@")[0]
            self.mailing_lists_names[key] = mail["display_name"]
            self.existing_messages[key] = []

    async def post_maillist(self):
        state_json = json.loads(STATE_JSON.read_text())
        mailing_lists = state_json.get(STATE_KEY)

        if not mailing_lists:
            return

        for maillist, thread_id in mailing_lists.items():
            thread_channel = await self.client.fetch_channel(thread_id)

            async with self.client.session.get(
                RECENT_THREADS_URL.format(name=maillist)
            ) as resp:
                recent = BeautifulSoup(await resp.text(), features="lxml")

            # When response have <p>, this mean that no activity in the mail
            if recent.p:
                continue

            for thread in recent.html.body.div.find_all("a", href=True):
                if "latest" in thread["href"]:
                    continue

                email_information = await self.get_first_mail(maillist, thread["href"].split("/")[-2])
                date_mail = datetime.strptime(email_information["date"], "%Y-%m-%dT%X%z")

                if (
                    self.mail_exists(email_information["message_id_hash"])
                    or "Re: " in email_information["subject"]
                    or date_mail.date() < (date.today() - timedelta(days=1))
                ):
                    continue

                content = email_information["content"]
                link = THREAD_URL.format(
                    id=thread["href"].split("/")[-2], list=maillist
                )

                embed = discord.Embed(
                    title=email_information["subject"],
                    description=content[:1000] + "..." if len(content) > 1000 else content,
                    timestamp=date_mail,
                    url=link,
                    colour=next(COLOURS),
                )
                embed.set_author(
                    name=f"{email_information['sender_name']} ({email_information['sender']['address']})",
                    url=MAILMAN_PROFILE_URL.format(
                        id=email_information["sender"]["mailman_id"]
                    ),
                )
                embed.set_footer(
                    text=self.mailing_lists_names[maillist],
                    icon_url="https://www.python.org/static/opengraph-icon-200x200.png",
                )
                msg = await thread_channel.send(embed=embed)

                if msg:
                    self.write_mail_hash(email_information["message_id_hash"])

    async def get_first_mail(self, mail_list, thread_identifier):
        """Get first mail from mail.python.org based on `mail_list` and `thread_identifier`."""
        async with self.client.session.get(
            THREAD_API_URL.format(name=mail_list, id=thread_identifier)
        ) as resp:
            thread_info = await resp.json()

        async with self.client.session.get(thread_info["starting_email"]) as resp:
            email_info = await resp.json()
        return email_info

    def cog_unload(self) -> None:
        self.fetch_new_posts.cancel()


async def setup(client) -> None:
    await client.add_cog(PythonMailingList(client))
