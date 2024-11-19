# bot/cogs/automation.py

import discord
from discord.ext import commands
from app.config import settings
from datetime import datetime, timedelta
import aiohttp
import asyncio
import io
import csv
import logging
import time

logger = logging.getLogger("bbrf_discord_bot")

class AutomationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def basicrecon(self, ctx, domain: str):
        """Run basic recon on a domain"""
        logger.info(f"User {ctx.author} requested basic recon for domain: {domain}")
        
        start_time = time.time()
        status_embed = discord.Embed(
            title="Basic Recon",
            description=f"Starting basic recon for **{domain}**. This may take a while...",
            color=0xFFFF00  # Yellow color
        )
        status_embed.add_field(name="Domain", value=domain, inline=False)
        status_embed.add_field(name="Time elapsed", value="0:00:00", inline=True)
        status_embed.add_field(name="Status", value="In Progress", inline=True)
        status_message = await ctx.send(embed=status_embed)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{settings.API_URL}/api/v1/automation/basic-recon', 
                                        json={'domain': domain},
                                        timeout=aiohttp.ClientTimeout(total=None)) as response:
                    if response.status == 200:
                        task_data = await response.json()
                        logger.debug(f"Basic recon task started for {domain}. Task ID: {task_data['task_id']}")
                        recon_results = await self.poll_recon_status(session, task_data['task_id'], status_message, domain, start_time)
                        if recon_results:
                            logger.info(f"Successfully completed basic recon for {domain}")
                            await self.update_final_embed(status_message, domain, recon_results, start_time)
                        else:
                            logger.warning(f"Basic recon failed or timed out for {domain}")
                            await self.update_embed_on_failure(status_message, f"Basic recon failed or timed out for **{domain}**.")
                    else:
                        error_message = f"Error starting basic recon: {response.status}"
                        logger.error(error_message)
                        await self.update_embed_on_failure(status_message, error_message)
        except Exception as e:
            error_message = f"An error occurred during basic recon: {str(e)}"
            logger.exception(error_message)
            await self.update_embed_on_failure(status_message, error_message)

    async def poll_recon_status(self, session, task_id, status_message, domain, start_time):
        poll_interval = 30  # seconds
        
        while True:
            try:
                async with session.get(f'{settings.API_URL}/api/v1/automation/task/{task_id}') as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Poll for task {task_id}: Status {data['status']}")
                        if data['status'] == 'completed':
                            return data.get('result', {})
                        elif data['status'] == 'in_progress':
                            elapsed_time = time.time() - start_time
                            progress = data.get('progress', 'In Progress')
                            await self.update_status_embed(status_message, domain, elapsed_time, progress)
                        elif data['status'] == 'failed':
                            error_message = f"Basic recon failed for **{domain}**: {data.get('error', 'Unknown error')}"
                            logger.error(error_message)
                            await self.update_embed_on_failure(status_message, error_message)
                            return None
                        else:
                            logger.error(f"Unexpected status for task {task_id}: {data['status']}")
                            return None
            except aiohttp.ClientError as e:
                logger.error(f"Error polling status for task {task_id}: {str(e)}")
            
            await asyncio.sleep(poll_interval)

    async def update_status_embed(self, message, domain, elapsed_time, progress):
        embed = message.embeds[0]
        embed.set_field_at(1, name="Time elapsed", value=str(timedelta(seconds=int(elapsed_time))), inline=True)
        embed.set_field_at(2, name="Status", value=progress, inline=True)
        await message.edit(embed=embed)

    async def update_final_embed(self, message, domain, results, start_time):
        elapsed_time = time.time() - start_time
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        
        embed = discord.Embed(
            title="Basic Recon Results",
            description=f"Completed basic recon for **{domain}**",
            color=0x00FF00  # Green color
        )
        embed.add_field(name="Domain", value=domain, inline=False)
        embed.add_field(name="Subdomains Added", value=str(results.get('subdomains_added', 'N/A')), inline=True)
        embed.add_field(name="DNS Results Added", value=str(results.get('dns_results_added', 'N/A')), inline=True)
        embed.add_field(name="HTTP Results Added", value=str(results.get('http_results_added', 'N/A')), inline=True)
        
        embed.add_field(name="Time taken", value=elapsed_str, inline=True)
        
        await message.edit(embed=embed)

    async def update_embed_on_failure(self, message, error_message):
        embed = discord.Embed(
            title="Basic Recon Error",
            description=error_message,
            color=0xFF0000  # Red color
        )
        try:
            await message.edit(embed=embed)
        except discord.HTTPException as e:
            logger.error(f"Failed to update error embed: {str(e)}")
            await message.edit(content="An error occurred during basic recon. Please check the logs for details.")

async def setup(bot):
    await bot.add_cog(AutomationCog(bot))
    logger.info("AutomationCog has been loaded")