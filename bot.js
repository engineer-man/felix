const discord = require('discord.js');
const bot = new discord.Client();

bot.on('message', message => {
    var content = message.content;

    if (content.match(/^(hi|what's up|yo|hey|hello) felix/gi)) {
        message.reply('hello!');
    }
});

bot.login('NDc5ODczMjUzMDA0MDE3NjY0.Dlfk_Q.IVhb40EqoYBQju7NFTOcPZMJr9I');
