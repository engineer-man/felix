import re
import asyncio
import aiohttp
import logging
from typing import List

# Discord.py Library
from discord import (
    Embed, 
    Colour,
    Reaction,
    Member
)
from discord.ext import commands

# CONSTANTS
PAGINATION_EMOJIS = ('◀️', '⏪', '⏹️', '▶️', '⏩')
log = logging.getLogger(__name__)

class Wikipedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def wiki_request(self, ctx, search: str) -> List[dict]:
        """-------------- WIKIPEDIA REQUEST --------------"""
        api = f'https://en.wikipedia.org/w/api.php?action=query&list=search&prop=info&inprop=url&utf8=&format=json&origin=*&srlimit=20&srsearch={search}'
        async with self.session.get(url=api) as response:
            if response.status == 200:
                request = await response.json()
                results_found = request['query']['searchinfo']['totalhits']
                if results_found:
                    filtered_request = request['query']['search'][:10]
                    formatted_request = []
                    for current_request in filtered_request: # save the first 10 search results in results
                        formatted_request.append({
                            'title' : current_request['title'],
                            'snippet' : re.sub(r'(<!--.*?-->|<[^>]*>)', '', current_request['snippet']),
                            'pageid' : current_request['pageid']
                        })
                    return formatted_request
                else:
                    await ctx.send('No results found') # If request['query']['search'] is False, return no results found
            else:
                await ctx.send('Whoops, the Wiki API is having some issues right now. Try again later') 

    async def pagination(self, ctx, contents):
        """-------------- EMBED PAGINATION BUILDER -------------- """
        embed_pages = []

        for info in contents:
            """  -------------- EMBED PAGE BUILDER --------------"""
            embed = Embed(
                title='Wikipedia Search', 
                description=f'[Link to page](https://en.wikipedia.org/?curid={info["pageid"]})', 
                colour=Colour.green()
            )
            embed.add_field(name=info['title'], value=info['snippet'])
            embed.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/330px-Wikipedia-logo-v2.svg.png')
            embed_pages.append(embed)
            log.trace(f"Appending '{embed.description}' to  embed pages")

        pagination_msg = await ctx.send(embed=embed_pages[0])

        # Add all the applicable emoji to the message
        for emoji in PAGINATION_EMOJIS:
            log.trace(f"Adding reaction: {repr(emoji)}")
            await pagination_msg.add_reaction(emoji)

        def check(reaction, user) -> bool:
            """-------------- MESSAGE REACTION CHECK --------------"""
            msg_pass = False
            user_pass = False
            channel_pass = False
            reaction_pass = False

            # Conditions for a successful pagination:
            if reaction.message.id == pagination_msg.id: # Reaction is on this message
                msg_pass = True                            
            if user.id == ctx.author.id: # Reaction was not made by the Bot
                user_pass = True
            if reaction.message.channel.id == pagination_msg.channel.id:
                channel_pass = True
            if str(reaction.emoji) in PAGINATION_EMOJIS: # Reaction is one of the pagination emotes
                reaction_pass = True

            return all([msg_pass, user_pass, channel_pass, reaction_pass])

        current_page = 0
        total_pages = len(embed_pages) - 1 # subtract 1 to use the index
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=300.0)
                log.trace(f"Got reaction: {reaction}")
            except asyncio.TimeoutError:
                log.debug("Timed out waiting for a reaction")
                await pagination_msg.clear_reactions() # We're done, no reactions for the last 5 minutess
                return
            else:
                if str(reaction.emoji) == '◀️':
                    current_page -= 1
                    if current_page < 0:
                        current_page = total_pages
                        log.debug(f"Got previous page reaction, but we're on the first page - changing to page {total_pages}/{total_pages}")
                    else:
                        log.debug(f"Got previous page reaction - changing to page {current_page}/{total_pages}")
                    await pagination_msg.remove_reaction('◀️', ctx.author)
                    await pagination_msg.edit(embed=embed_pages[current_page])

                elif str(reaction.emoji) == '▶️':
                    current_page += 1
                    if current_page > total_pages:
                        log.debug(f"Got next page reaction, but we're on the last page - changing to page 0/{total_pages}")
                        current_page = 0
                    else:
                        log.debug(f"Got next page reaction - changing to page {current_page}/{total_pages}")
                    await pagination_msg.remove_reaction('▶️', ctx.author)
                    await pagination_msg.edit(embed=embed_pages[current_page])
                
                elif str(reaction.emoji) == '⏪':
                    current_page = 0
                    log.debug(f"Got first page reaction - changing to page {current_page}/{total_pages}")
                    await pagination_msg.remove_reaction('⏪', ctx.author)
                    await pagination_msg.edit(embed=embed_pages[current_page])
                
                elif str(reaction.emoji) == '⏩':
                    current_page = total_pages
                    log.debug(f"Got last page reaction - changing to page {current_page}/{total_pages}")
                    await pagination_msg.remove_reaction('⏩', ctx.author)
                    await pagination_msg.edit(embed=embed_pages[current_page])
                
                elif str(reaction.emoji) == '⏹️':
                    log.debug("Got delete reaction")
                    await pagination_msg.delete()
                    return

        log.debug("Ending pagination and clearing reactions...")
        

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="wiki", aliases=["wikipedia"])
    async def wiki(self, ctx, *, search):
        contents = await self.wiki_request(ctx, search)
        if contents:
            await self.pagination(ctx, contents)

def setup(bot: commands.Bot) -> None:
    """ Adding Wikipedia Cog"""
    bot.add_cog(Wikipedia(bot))