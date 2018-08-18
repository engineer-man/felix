require('nocamel');

const config = require('./config');
const discord = require('discord.js');
const request = require('request-promise');
const q = require('q');

const bot = new discord.Client();

bot.on('message', message => {
    var content = message.content;
    var channel = message.channel;

    if (content.match(/^(hi|what's up|yo|hey|hello) felix/gi)) {
        message.reply('hello!');
    }

    if (content.match(/^felix poll/gi)) {
        var questions = content
            .split('\n')
            .filter(l => l.match(/^[0-9]+/gi))
            .length;

        questions = questions > 9 ? 9 : questions;

        var map = {
            1: '\u0031\u20E3',
            2: '\u0032\u20E3',
            3: '\u0033\u20E3',
            4: '\u0034\u20E3',
            5: '\u0035\u20E3',
            6: '\u0036\u20E3',
            7: '\u0037\u20E3',
            8: '\u0038\u20E3',
            9: '\u0039\u20E3',
        };

        var reactions = [];

        for (var i = 0; i < questions; ++i) {
            reactions.push(map[i+1]);
        }

        var chain = q.fcall(() => {});

        reactions.for_each(r => {
            chain = chain
                .then(() => {
                    return message.react(r);
                });
        });
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
