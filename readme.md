# Felix
Felix Discord Bot

## Getting started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites
* **Python 3.6** or higher
* **Node.js 8.10.0** or higher

### Installing
```
git clone https://github.com/engineer-man/felix.git
cd felix
cd node
npm install
cd ..
pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py
```
Duplicate `config.json.sample` and rename it `config.json` and update it with your own discord bot token.

### Running the bot
```
./start
```

### Creating your own bot extension
This bot uses the `discord.py rewrite API` (https://discordpy.readthedocs.io/en/rewrite/api.html)

You can create new bot commands or tasks by creating your own extension/cog.

A `sample_cog.py` is included inside the `python/extension` folder.

If you have questions visit us on our discord: https://engineerman.org/discord
To ask questions and see felix in action.
