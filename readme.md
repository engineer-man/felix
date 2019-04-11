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
pip install -U discord.py
```
Duplicate `config.json.sample` and rename it `config.json` and update it with your own discord bot token.

Duplicate `state.json.sample` and rename it `state.json`.

### Running the bot
Using python
```
cd python
python3 bot.py
```
Using Docker
```
docker-compose up
```

### Creating your own python bot extension (cog)
This bot uses the `discord.py API wrapper` (https://rapptz.github.io/discord.py/docs/index.html)

You can create new bot commands or tasks by creating your own extension/cog.

A `sample_cog.py` is included inside the `python/extension` folder.

### Contributing to Felix
If you want to contribute to Felix you can just submit a pull request.
#### Code styling / IDE Settings
Please style your code according to these guidelines when writing python code for Felix:
* maximum line length is 80 columns 
* use 4 spaces for indentation
* files end with a newline 
* lines should not have trailing whitespace

If you want to use an auto formatter please use `autopep8`

Example config for VSCode:
```
"[python]": {
    "editor.rulers": [
        80
    ],
    "editor.tabSize": 4,
},
"files.insertFinalNewline": true,
"files.trimTrailingWhitespace": true,
"editor.trimAutoWhitespace": true,
"python.formatting.provider": "autopep8",
```

You can visit us on our discord: https://discord.gg/engineerman
 to ask questions and see felix in action.
