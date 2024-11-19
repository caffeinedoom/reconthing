# bot/cogs/http.py

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from app.config import settings
import aiohttp
import asyncio
import io
import csv
import logging
import time

logger = logging.getLogger("bbrf_discord_bot")

class HTTPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def http(self, ctx, domain: str, *args):
        """Perform HTTP probing for a given domain"""
        logger.info(f"User {ctx.author} requested HTTP probing for domain: {domain}")
        use_csv = "-csv" in args
        
        start_time = time.time()
        status_embed = discord.Embed(
            title="HTTP Probing",
            description=f"Starting HTTP probing for **{domain}**. This may take a while...",
            color=0xFFFF00  # Yellow color
        )
        status_embed.add_field(name="Domain", value=domain, inline=False)
        status_embed.add_field(name="Time elapsed", value="0:00:00", inline=True)
        status_embed.add_field(name="Probes completed", value="0", inline=True)
        status_message = await ctx.send(embed=status_embed)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{settings.API_URL}/api/v1/http/probe', 
                                        json={'domain': domain},
                                        timeout=aiohttp.ClientTimeout(total=None)) as response:
                    if response.status == 200:
                        task_data = await response.json()
                        logger.debug(f"HTTP probing task started for {domain}. Task ID: {task_data['task_id']}")
                        probe_results = await self.poll_probe_status(session, task_data['task_id'], status_message, domain, start_time)
                        if probe_results:
                            logger.info(f"Successfully probed {len(probe_results)} URLs for {domain}")
                            await self.update_final_embed(status_message, domain, probe_results, use_csv, start_time)
                        else:
                            logger.warning(f"HTTP probing failed, no domains, or timed out for {domain}")
                            await self.update_embed_on_failure(status_message, f"HTTP probing failed or timed out for **{domain}**.")
                    else:
                        error_message = f"Error starting HTTP probing: {response.status}"
                        logger.error(error_message)
                        await self.update_embed_on_failure(status_message, error_message)
        except Exception as e:
            error_message = f"An error occurred during HTTP probing: {str(e)}"
            logger.exception(error_message)
            await self.update_embed_on_failure(status_message, error_message)

    @commands.command()
    async def gethttp(self, ctx, domain: str, *args):
        """Get stored HTTP probe results for a given domain"""
        logger.info(f"User {ctx.author} requested stored HTTP probe results for domain: {domain}")
        use_csv = "-csv" in args
        start_time = time.time()

        status_embed = discord.Embed(
            title="Retrieving Stored HTTP Probe Results",
            description=f"Fetching stored HTTP probe results for **{domain}**...",
            color=0xFFFF00  # Yellow color
        )
        status_message = await ctx.send(embed=status_embed)

        async with aiohttp.ClientSession() as session:
            try:
                url = f'{settings.API_URL}/api/v1/http/probe/results/{domain}'
                async with session.get(url) as response:
                    if response.status == 200:
                        probe_results = await response.json()
                        logger.info(f"Successfully retrieved HTTP probe results for {domain}")
                        await self.update_final_embed(status_message, domain, probe_results, use_csv, start_time)
                    elif response.status == 404:
                        message = f"No HTTP probe results found for **{domain}**"
                        logger.warning(message)
                        await self.update_embed_on_failure(status_message, message)
                    else:
                        error_message = f"Error retrieving HTTP probe results: {response.status}"
                        logger.error(error_message)
                        await self.update_embed_on_failure(status_message, error_message)
            except aiohttp.ClientError as e:
                error_message = f"Error connecting to API: {str(e)}"
                logger.exception(error_message)
                await self.update_embed_on_failure(status_message, error_message)

    async def poll_probe_status(self, session, task_id, status_message, domain, start_time):
        poll_interval = 30  # seconds
        
        while True:
            try:
                async with session.get(f'{settings.API_URL}/api/v1/http/probe/status/{task_id}') as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Poll for task {task_id}: Status {data['status']}")
                        if data['status'] == 'completed':
                            return data.get('probes', [])
                        elif data['status'] == 'in_progress':
                            elapsed_time = time.time() - start_time
                            probes = data.get('probes', [])
                            probe_count = len(probes) if probes is not None else 0
                            await self.update_status_embed(status_message, domain, elapsed_time, probe_count)
                        elif data['status'] == 'failed':
                            error_message = f"HTTP probing failed for **{domain}**: {data.get('error', 'Unknown error')}"
                            logger.error(error_message)
                            await self.update_embed_on_failure(status_message, error_message)
                            return []
                        else:
                            logger.error(f"Unexpected status for task {task_id}: {data['status']}")
                            return []
            except aiohttp.ClientError as e:
                logger.error(f"Error polling status for task {task_id}: {str(e)}")
            
            await asyncio.sleep(poll_interval)

    async def update_status_embed(self, message, domain, elapsed_time, probe_count):
        embed = message.embeds[0]
        embed.set_field_at(1, name="Time elapsed", value=str(timedelta(seconds=int(elapsed_time))), inline=True)
        embed.set_field_at(2, name="Probes completed", value=str(probe_count), inline=True)
        await message.edit(embed=embed)

    async def update_final_embed(self, message, domain, probe_results, use_csv, start_time):
        elapsed_time = time.time() - start_time
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        total_probes = len(probe_results)
        
        embed = discord.Embed(
            title="HTTP Probe Results",
            description=f"Retrieved HTTP probe results for **{domain}**",
            color=0x00FF00  # Green color
        )
        embed.add_field(name="Domain", value=domain, inline=False)
        embed.add_field(name="Total Probes", value=str(total_probes), inline=True)
        embed.add_field(name="Time taken", value=elapsed_str, inline=True)
        
        file_type = "CSV" if use_csv else "text"
        file = self.create_file(probe_results, domain, use_csv)
        
        embed.add_field(name="File Type", value=file_type, inline=True)
        
        await message.edit(embed=embed)
        await message.channel.send(f"Please find the complete list of HTTP probe results in the attached {file_type} file.", file=file)

    async def update_embed_on_failure(self, message, error_message):
        embed = discord.Embed(
            title="HTTP Probing Error",
            description=error_message,
            color=0xFF0000  # Red color
        )
        try:
            await message.edit(embed=embed)
        except discord.HTTPException as e:
            logger.error(f"Failed to update error embed: {str(e)}")
            await message.edit(content="An error occurred during HTTP probing. Please check the logs for details.")

    def create_file(self, probe_results, domain, use_csv):
        if use_csv:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Domain", "URL", "Status Code", "Title", "Content Length", "Technologies", "Webserver", "IP Address"])
            for result in probe_results:
                writer.writerow([
                    domain,
                    result['url'],
                    result.get('status_code', 'N/A'),
                    result.get('title', 'N/A'),
                    result.get('content_length', 'N/A'),
                    ', '.join(result.get('technologies', []) or []),  # Added default empty list
                    result.get('webserver', 'N/A'),
                    result.get('ip_address', 'N/A')
                ])
            output.seek(0)
            return discord.File(output, filename=f"{domain}_http_probe_results.csv")
        else:
            # For text output, only include URLs
            file_content = "\n".join([result['url'] for result in probe_results])
            return discord.File(io.StringIO(file_content), filename=f"{domain}_http_probe_results.txt")

async def setup(bot):
    await bot.add_cog(HTTPCog(bot))
    logger.info("HTTPCog has been loaded") 