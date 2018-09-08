require('nocamel');

const config = require('./config');
const discord = require('discord.js');
const fs = require('fs');
const request = require('request-promise');
const q = require('q');

const bot = new discord.Client();

var state = {
    hangman_solver: true
};

var dictionary = fs.readFileSync('/usr/share/dict/lwords').toString().split('\n');

console.log('starting')

bot.on('guildMemberAdd', member => {
    const channel = member.guild.channels.find(ch => ch.name === 'welcome');

    channel.send(
        'Welcome to the Engineer Man Community Discord Server, ' + member + '. ' +
        'I\'m Felix, the server smart assistant. You can learn more about what I can do by saying `felix help`. ' +
        'You can view the server rules @ <#484103976296644608>. Please be kind and decent to one another. ' +
        'Glad you\'re here!'
    );
});

bot.on('message', message => {
    var content = message.content;
    var channel = message.channel;

    switch (content) {
        case 'felix help':
            if (message.author.bot) break;

            var help =
                'hi, here is what i can do:\n' +
                '\n' +
                'felix gif [gif name here]\n' +
                'felix google [google search term]';

            if (channel.name === 'staff-room') {
                help +=
                    '\n\n' +
                    'mod only:\n' +
                    'felix poll [newline then 1. 2. etc]\n' +
                    'felix purge [number of messaged to delete]'
            }

            channel.send(help);
            break;
        case 'html is a programming language':
            message.reply('no it\'s not, don\'t be silly');
            break;
        case 'you wanna fight, felix?':
            message.reply('bring it on pal (╯°□°）╯︵ ┻━┻');
            break;
    }

    if (content.match(/^(hi|what's up|yo|hey|hello) felix/gi)) {
        message.reply('hello!');
    }

    if (content.match(/^felix enable/gi)) {
        var mode = content.split('enable')[1].trim();

        state[mode] = true;

        message.reply(mode + ' enabled');
    }

    if (content.match(/^felix disable/gi)) {
        var mode = content.split('disable')[1].trim();

        state[mode] = false;

        message.reply(mode + ' disabled');
    }

    if (message.channel.name === 'em-hangman' &&
        state.hangman_solver &&
        message.embeds.length > 0 &&
        ~message.embeds[0].description.indexOf('your word')) {

        var description = message.embeds[0].description;
        var word_row = ' ' + description
            .split('\n')
            .filter(r => r.match(/^your word is/gi))[0]
            .replace('your word is:', '')
            .replace(/\\/gi, '')
            .trim();

        var incorrect = description
            .split('\n')
            .filter(r => r.trim().match(/^incorrect/gi));

        if (incorrect.length > 0) {
            incorrect = incorrect[0]
                .split(':')[1]
                .trim()
                .split('');
        }

        var correct = description
            .split('\n')
            .filter(r => r.trim().match(/^correct/gi));

        if (correct.length > 0) {
            correct = correct[0]
                .split(':')[1]
                .trim()
                .split('');
        }

        var word_len = 0;
        var word_map = [];
        var missing_idx = [];

        for (var i = 0; i < word_row.length; ++i) {
            if (word_row[i] === ' ') {
                ++word_len;
                ++i;
                word_map.push(word_row[i]);
                if (word_row[i] === '_') {
                    missing_idx.push(word_map.length-1);
                }
            }
        }

        var valid_words = [];

        dictionary.for_each(word => {
            if (word.length !== word_len) return null;
            if (word.match(/[0-9\-]+/gi)) return null;
            if (~incorrect.index_of(word)) return null;

            for (var i = 0; i < word_map.length; ++i) {
                if (word_map[i] === '_') continue;
                if (word[i] !== word_map[i]) return null;
            }

            valid_words.push(word);
        });

        var letters = {
            a: 0, b: 0, c: 0, d: 0, e: 0, f: 0, g: 0, h: 0,
            i: 0, j: 0, k: 0, l: 0, m: 0, n: 0, o: 0, p: 0,
            q: 0, r: 0, s: 0, t: 0, u: 0, v: 0, w: 0, x: 0,
            y: 0, z: 0,
        };

        for (var x = 0; x < valid_words.length; ++x) {
            for (var i = 0; i < valid_words[x].length; ++i) {
                ++letters[valid_words[x][i]];
            }
        }

        incorrect.for_each(c => delete letters[c]);
        correct.for_each(c => delete letters[c]);

        var letter = null;
        var letter_c = -1;

        Object.keys(letters).for_each(key => {
            if (letters[key] < letter_c || !key.match(/[a-z\-]/gi)) return null;
            letter = key;
            letter_c = letters[key];
        });

        channel.send('duckie letter ' + letter);
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

    if (content.match(/^felix google/gi)) {
        var text = content.split('google')[1].trim();

        channel.send('here you go! <https://www.google.com/search?q=' + text.split(' ').join('+') + '>');
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
                    '&q=' + text.split(' ').join('+') +
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
                    channel.send('sorry, no gif found for: ' + text);
                    return null;
                }

                var gif = data[0].images.original.url;

                channel.send(gif);
            })
            .catch(err => {
                channel.send('sorry, you broke me, no gifs right now :(');
            });
    }

    if (content.match(/^felix purge [0-9]+/gi)) {
        var roles = message.member.roles.map(r => r.name);

        var allowed = false;

        ['engineer man', 'admins', 'moderators'].for_each(r => {
            if (~roles.index_of(r)) allowed = true;
        });

        if (!allowed) return null;

        var limit = +content.split('purge')[1].trim();

        if (limit <= 0 || typeof limit !== 'number') return null;

        channel.fetchMessages({limit: limit + 1})
            .then(messages => {
                channel.bulkDelete(messages);
            });
    }
});

bot.login(config.bot_key);
