"""This is a cog for a discord.py bot.
It checks git periodically for new commits in specific repositories
and post them into specified channels.

Put the settings into the .settings file with the same name.

Load the cog by calling client.load_extension with the name of this python file
as an argument (without .py)
    example:    bot.load_extension('filename')
or by calling it with the path and the name of this python file
    example:    bot.load_extension('my_extensions.filename')
"""

from discord.ext import commands
import json
import asyncio
import requests


class GitHubMonitor():
    def __init__(self, client):
        self.client = client
        with open(__file__.replace('.py', '.settings')) as f:
            settings = json.load(f)
            self.repositories = settings['repositories']
            self.frequency = settings['frequency']
            self.token = settings['token']
            self.targets = settings['targets']
        self.task = self.client.loop.create_task(self.github_monitor())

    async def on_ready(self):
        pass

    async def github_monitor(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(5)
        try:
            while not self.client.is_closed():
                api_dict = self.get_from_api()
                file_dict = self.get_from_history()
                save_dict = {}
                for r, current_commits in api_dict.items():
                    known_commits = file_dict.get(r, [])
                    new_shas = [x['sha'] for x in current_commits]
                    is_all_known = all(sha in known_commits for sha in new_shas)
                    if not known_commits or is_all_known:
                        save_dict[r] = new_shas
                        continue
                    for c in current_commits:
                        if c['sha'] not in known_commits:
                            await self.send_to_targets(c['html_url'])
                    save_dict[r] = new_shas
                self.save_history_to_file(save_dict)

                await asyncio.sleep(self.frequency)
        except asyncio.CancelledError:
            pass

    async def send_to_targets(self, txt):
        for target in self.targets:
            to_guild = self.client.get_guild(target[0])
            to_chat = to_guild.get_channel(target[1])
            await to_chat.send(txt)

    def get_from_api(self):
        repos = {}
        headers = {'Authorization': f'token {self.token}'}
        for repname in self.repositories:
            repo = []
            nxt = f'https://api.github.com/repos/{repname}/commits?per_page=100'
            while nxt:
                r = requests.get(nxt, headers=headers)
                repo += r.json()
                try:
                    nxt = r.links['next']['url']
                except:
                    nxt = ''
            repos[repname] = list(reversed(repo))

        return repos

    def get_from_history(self):
        try:
            with open(__file__.replace('.py', '.history')) as f:
                repos = json.load(f)
        except:
            repos = {}
        return repos

    def save_history_to_file(self, o):
        with open(__file__.replace('.py', '.history'), 'w') as f:
            json.dump(o, f, indent=1)

    def __unload(self):
        self.task.cancel()


def setup(client):
    client.add_cog(GitHubMonitor(client))

def teardown(client):
    pass
