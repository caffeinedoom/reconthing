# bot/cogs/subdomain.py

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

class SubdomainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def subdomain(self, ctx, domain: str, *args):
        """Enumerate subdomains for a given domain"""
        logger.info(f"User {ctx.author} requested subdomain enumeration for domain: {domain}")
        use_csv = "-csv" in args
        
        start_time = time.time()
        status_embed = discord.Embed(
            title="Subdomain Enumeration",
            description=f"Starting subdomain enumeration for **{domain}**. This may take a while...",
            color=0xFFFF00  # Yellow color
        )
        status_embed.add_field(name="Domain", value=domain, inline=False)
        status_embed.add_field(name="Time elapsed", value="0:00:00", inline=True)
        status_embed.add_field(name="Subdomains found", value="0", inline=True)
        status_message = await ctx.send(embed=status_embed)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{settings.API_URL}/api/v1/enumerate', 
                                        json={'domain': domain},
                                        timeout=aiohttp.ClientTimeout(total=None)) as response:
                    if response.status == 200:
                        task_data = await response.json()
                        logger.debug(f"Enumeration task started for {domain}. Task ID: {task_data['task_id']}")
                        subdomains = await self.poll_enumeration_status(session, task_data['task_id'], status_message, domain, start_time)
                        if subdomains:
                            logger.info(f"Successfully enumerated {len(subdomains)} subdomains for {domain}")
                            await self.update_final_embed(status_message, domain, subdomains, use_csv, start_time)
                        else:
                            logger.warning(f"Enumeration failed or timed out for {domain}")
                            await self.update_embed_on_failure(status_message, f"Enumeration failed or timed out for **{domain}**.")
                    else:
                        error_message = f"Error starting enumeration: {response.status}"
                        logger.error(error_message)
                        await self.update_embed_on_failure(status_message, error_message)
        except Exception as e:
            error_message = f"An error occurred during subdomain enumeration: {str(e)}"
            logger.exception(error_message)
            await self.update_embed_on_failure(status_message, error_message)

    async def poll_enumeration_status(self, session, task_id, status_message, domain, start_time):
        poll_interval = 5  # seconds
        max_polls = 60  # 5 minutes max waiting time
        
        for poll_count in range(max_polls):
            try:
                async with session.get(f'{settings.API_URL}/api/v1/enumerate/status/{task_id}') as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Poll {poll_count + 1} for task {task_id}: Status {data['status']}")
                        if data['status'] == 'completed':
                            return data['subdomains']
                        elif data['status'] == 'in_progress':
                            elapsed_time = time.time() - start_time
                            await self.update_status_embed(status_message, domain, elapsed_time, len(data.get('subdomains', [])))
                        elif data['status'] == 'failed':
                            error_message = f"Enumeration failed for **{domain}**: {data.get('error', 'Unknown error')}"
                            logger.error(error_message)
                            await self.update_embed_on_failure(status_message, error_message)
                            return None
                        else:
                            logger.error(f"Unexpected status for task {task_id}: {data['status']}")
                            return None
            except aiohttp.ClientError as e:
                logger.error(f"Error polling status for task {task_id}: {str(e)}")
            await asyncio.sleep(poll_interval)
        
        logger.warning(f"Enumeration timed out after {max_polls * poll_interval} seconds for task {task_id}")
        await self.update_embed_on_failure(status_message, f"Enumeration for **{domain}** is taking longer than expected. Please check back later.")
        return None

    async def update_status_embed(self, message, domain, elapsed_time, subdomain_count):
        embed = message.embeds[0]
        embed.set_field_at(1, name="Time elapsed", value=str(timedelta(seconds=int(elapsed_time))), inline=True)
        embed.set_field_at(2, name="Subdomains found", value=str(subdomain_count), inline=True)
        await message.edit(embed=embed)

    async def update_final_embed(self, message, domain, subdomains, use_csv, start_time):
        elapsed_time = time.time() - start_time
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        total_subdomains = len(subdomains)
        
        embed = message.embeds[0]
        embed.color = 0x00FF00  # Green color
        embed.title = "Enumerated Subdomains"
        embed.description = f"Subdomain enumeration completed for **{domain}**"
        embed.clear_fields()
        embed.add_field(name="Domain", value=domain, inline=False)
        embed.add_field(name="Total Subdomains", value=str(total_subdomains), inline=True)
        embed.add_field(name="Time taken", value=elapsed_str, inline=True)
        
        file_type = "CSV" if use_csv else "text"
        file = self.create_csv_file(subdomains, domain) if use_csv else self.create_txt_file(subdomains, domain)
        
        embed.add_field(name="File Type", value=file_type, inline=True)
        
        await message.edit(embed=embed)
        await message.channel.send(f"Please find the complete list of subdomains in the attached {file_type} file.", file=file)

    async def update_embed_on_failure(self, message, error_message):
        embed = message.embeds[0]
        embed.color = 0xFF0000  # Red color
        embed.description = error_message
        await message.edit(embed=embed)

    @commands.command()
    async def getsubdomain(self, ctx, domain: str, *args):
        """Get stored subdomains for a given domain"""
        logger.info(f"User {ctx.author} requested stored subdomains for domain: {domain}")
        use_csv = "-csv" in args
        start_time = time.time()

        status_embed = discord.Embed(
            title="Retrieving Stored Subdomains",
            description=f"Fetching stored subdomains for **{domain}**...",
            color=0xFFFF00  # Yellow color
        )
        status_message = await ctx.send(embed=status_embed)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'{settings.API_URL}/api/v1/subdomains/{domain}') as response:
                    if response.status == 200:
                        subdomains = await response.json()
                        logger.info(f"Successfully retrieved {len(subdomains)} subdomains for {domain}")
                        await self.update_final_embed(status_message, domain, subdomains, use_csv, start_time)
                    elif response.status == 404:
                        message = f"No subdomains found for **{domain}**"
                        logger.warning(message)
                        await self.update_embed_on_failure(status_message, message)
                    else:
                        error_message = f"Error retrieving subdomains: {response.status}"
                        logger.error(error_message)
                        await self.update_embed_on_failure(status_message, error_message)
            except aiohttp.ClientError as e:
                error_message = f"Error connecting to API: {str(e)}"
                logger.exception(error_message)
                await self.update_embed_on_failure(status_message, error_message)

    def create_txt_file(self, subdomains, domain):
        if isinstance(subdomains[0], dict):
            subdomain_list = [sub["subdomain"] for sub in subdomains]
        else:
            subdomain_list = subdomains
        file_content = "\n".join(subdomain_list)
        logger.debug(f"Created TXT file for {domain} with {len(subdomain_list)} subdomains")
        return discord.File(io.StringIO(file_content), filename=f"{domain}_subdomains.txt")

    def create_csv_file(self, subdomains, domain):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Domain", "Subdomain"])  # Removed "Created At" from header
        if isinstance(subdomains[0], dict):
            for subdomain in subdomains:
                writer.writerow([
                    subdomain.get("domain", domain),
                    subdomain.get("subdomain", "N/A")
                ])
        else:
            for subdomain in subdomains:
                writer.writerow([domain, subdomain])  # No need for "N/A" as third column
        output.seek(0)
        logger.debug(f"Created CSV file for {domain} with {len(subdomains)} subdomains")
        return discord.File(output, filename=f"{domain}_subdomains.csv")

async def setup(bot):
    await bot.add_cog(SubdomainCog(bot))
    logger.info("SubdomainCog has been loaded")