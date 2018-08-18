const config = require('./config');
const discord = require('discord.js');
const request = require('request-promise');
const bot = new discord.Client();

bot.on('message', message => {
    var content = message.content;
    var channel = message.channel;

    if (content.match(/^(hi|what's up|yo|hey|hello) felix/gi)) {
        message.reply('hello!');
    }

    if (content.match(/^felix gif /gi)) {
        message.reply('coming right up boss!');

        var text = content.split('gif')[1].trim();

        return request
            ({
                method: 'get',
                url:
                    'https://api.giphy.com/v1/gifs/search' +
                    '?api_key=' + config.giphy_key +
                    '&q=' + text +
                    '&limit=1' +
                    '&offset=0' +
                    '&rating=R' +
                    '&lang=en',
                json: true,
                simple: true
            })
            .then(res => {
                var data = res.data;

                if (data.length <= 0) {
                    // no gif
                }

                var gif = data[0].images.original.url;

                channel.send(gif);
            });
    }
});

bot.login(config.bot_key);
