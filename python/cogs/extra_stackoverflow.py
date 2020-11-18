import re
import asyncio
import aiohttp
import logging
from urllib.parse import quote
from typing import List
from html.parser import HTMLParser

# Discord.py Library
from discord import (
    Embed, 
    Colour,
    Reaction,
    Member
)
from discord.ext import commands

# CONSTANTS
PAGINATION_EMOJIS = ('⏪', '◀️', '⏹️', '▶️', '⏩')
log = logging.getLogger(__name__)

class Stackoverflow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def stack_request(self, ctx, title: str) -> List[dict]:
        """-------------- STACKOVERFLOW REQUEST --------------"""
        title = quote(title)
        filtered_request = {}
        api = f"https://api.stackexchange.com/2.2/search/advanced?key=U4DMV*8nvpm3EOpvf69Rxw((&site=stackoverflow&order=desc&sort=votes&closed=False&title={title}&filter=default"
        print(api)
        async with self.session.get(url=api) as response:
            if response.status == 200:
                request = await response.json()
                results_found = request["items"]
                print(results_found)
                if results_found:
                    formatted_request = []
                    for result in results_found:
                        try:
                            filtered_request[result['accepted_answer_id']] = result
                        except KeyError:
                            continue
                    for current_request in filtered_request: # save the first 10 search results in results
                        formatted_request.append({
                            'title' : HTMLParser().unescape(filtered_request.get(current_request)['title']),
                            'tags' :  filtered_request.get(current_request)['tags'],
                            'Link' : filtered_request.get(current_request)['link'],
                            'ViewCount' :  filtered_request.get(current_request)['view_count']                            
                        })
                    return formatted_request
                else:
                    await ctx.send('No results found') # If request['query']['search'] is False, return no results found
            else:
                await ctx.send('Whoops, the Stackoverflow API is having some issues right now. Try again later') 

    async def pagination(self, ctx, content):
        """-------------- EMBED PAGINATION BUILDER -------------- """
        embed_pages = []

        for x in range(0, len(content), 3):
            """  -------------- EMBED PAGE BUILDER --------------"""
            embed = Embed(
                title='Stackoverflow Search',
                colour=Colour.green()
            )
            try:
                embed.add_field(name='Title: '+content[x]['title'], value=f"[Tags: "+', '.join(tag for tag in content[x]['tags']) + f"]({content[x]['Link']})", inline=False)
                embed.add_field(name='Title: '+content[x+1]['title'], value=f"[Tags: "+', '.join(tag for tag in content[x+1]['tags']) + f"]({content[x]['Link']})", inline=False)
                embed.add_field(name='Title: '+content[x+2]['title'], value=f"[Tags: "+', '.join(tag for tag in content[x+2]['tags']) + f"]({content[x]['Link']})", inline=False)
            except IndexError:
                continue
            embed.set_thumbnail(url='https://camo.githubusercontent.com/db5c28745fde3010e4f8d24e6b2cdbf604362ee7/68747470733a2f2f67697465652e636f6d2f7961646f6e672e7a68616e672f7374617469632f7261772f6d61737465722f4a757374417574682f737461636b6f766572666c6f772e706e67')
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
                    await pagination_msg.clear_reactions()
                    return

        log.debug("Ending pagination and clearing reactions...")
        

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="stackoverflow", aliases=["stack", "stacko"])
    async def stackoverflow(self, ctx, *, search):
        contents = await self.stack_request(ctx, search)
        if contents:
            await self.pagination(ctx, contents)

def setup(bot: commands.Bot) -> None:
    """ Adding Stackoverflow Cog"""
    bot.add_cog(Stackoverflow(bot))
