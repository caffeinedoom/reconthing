# bot/cogs/dns.py

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

class DNSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def dns(self, ctx, domain: str, *args):
        """Resolve DNS for a given domain"""
        logger.info(f"User {ctx.author} requested DNS resolution for domain: {domain}")
        use_csv = "-csv" in args
        use_all = "-all" in args
        
        start_time = time.time()
        status_embed = discord.Embed(
            title="DNS Resolution",
            description=f"Starting DNS resolution for **{domain}**. This may take a while...",
            color=0xFFFF00  # Yellow color
        )
        status_embed.add_field(name="Domain", value=domain, inline=False)
        status_embed.add_field(name="Time elapsed", value="0:00:00", inline=True)
        status_embed.add_field(name="Resolutions found", value="0", inline=True)
        status_message = await ctx.send(embed=status_embed)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{settings.API_URL}/api/v1/dns/resolve', 
                                        json={'domain': domain},
                                        timeout=aiohttp.ClientTimeout(total=None)) as response:
                    if response.status == 200:
                        task_data = await response.json()
                        logger.debug(f"DNS resolution task started for {domain}. Task ID: {task_data['task_id']}")
                        resolutions = await self.poll_resolution_status(session, task_data['task_id'], status_message, domain, start_time)
                        if resolutions:
                            logger.info(f"Successfully resolved {len(resolutions)} DNS records for {domain}")
                            await self.update_final_embed(status_message, domain, resolutions, use_csv, use_all, start_time)
                        else:
                            logger.warning(f"DNS resolution failed or timed out for {domain}")
                            await self.update_embed_on_failure(status_message, f"DNS resolution failed or timed out for **{domain}**.")
                    else:
                        error_message = f"Error starting DNS resolution: {response.status}"
                        logger.error(error_message)
                        await self.update_embed_on_failure(status_message, error_message)
        except Exception as e:
            error_message = f"An error occurred during DNS resolution: {str(e)}"
            logger.exception(error_message)
            await self.update_embed_on_failure(status_message, error_message)

    @commands.command()
    async def getdns(self, ctx, domain: str, *args):
        """Get stored DNS resolutions for a given domain"""
        logger.info(f"User {ctx.author} requested stored DNS resolutions for domain: {domain}")
        use_csv = "-csv" in args
        use_all = "-all" in args
        start_time = time.time()

        status_embed = discord.Embed(
            title="Retrieving Stored DNS Resolutions",
            description=f"Fetching stored DNS resolutions for **{domain}**...",
            color=0xFFFF00  # Yellow color
        )
        status_message = await ctx.send(embed=status_embed)

        async with aiohttp.ClientSession() as session:
            try:
                if use_all:
                    url = f'{settings.API_URL}/api/v1/dns/subdomains-with-resolutions/{domain}'
                else:
                    url = f'{settings.API_URL}/api/v1/dns/resolutions/{domain}'
                
                async with session.get(url) as response:
                    if response.status == 200:
                        resolutions = await response.json()
                        logger.info(f"Successfully retrieved DNS resolutions for {domain}")
                        await self.update_final_embed(status_message, domain, resolutions, use_csv, use_all, start_time)
                    elif response.status == 404:
                        message = f"No DNS resolutions found for **{domain}**"
                        logger.warning(message)
                        await self.update_embed_on_failure(status_message, message)
                    else:
                        error_message = f"Error retrieving DNS resolutions: {response.status}"
                        logger.error(error_message)
                        await self.update_embed_on_failure(status_message, error_message)
            except aiohttp.ClientError as e:
                error_message = f"Error connecting to API: {str(e)}"
                logger.exception(error_message)
                await self.update_embed_on_failure(status_message, error_message)

    async def poll_resolution_status(self, session, task_id, status_message, domain, start_time):
        poll_interval = 30  # seconds, increased to reduce API load
        
        while True:
            try:
                async with session.get(f'{settings.API_URL}/api/v1/dns/resolve/status/{task_id}') as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Poll for task {task_id}: Status {data['status']}")
                        if data['status'] == 'completed':
                            return data.get('resolutions', [])
                        elif data['status'] == 'in_progress':
                            elapsed_time = time.time() - start_time
                            resolutions = data.get('resolutions', [])
                            resolution_count = len(resolutions) if resolutions is not None else 0
                            await self.update_status_embed(status_message, domain, elapsed_time, resolution_count)
                        elif data['status'] == 'failed':
                            error_message = f"DNS resolution failed for **{domain}**: {data.get('error', 'Unknown error')}"
                            logger.error(error_message)
                            await self.update_embed_on_failure(status_message, error_message)
                            return []
                        else:
                            logger.error(f"Unexpected status for task {task_id}: {data['status']}")
                            return []
            except aiohttp.ClientError as e:
                logger.error(f"Error polling status for task {task_id}: {str(e)}")
            
            await asyncio.sleep(poll_interval)

    async def update_status_embed(self, message, domain, elapsed_time, resolution_count):
        embed = message.embeds[0]
        embed.set_field_at(1, name="Time elapsed", value=str(timedelta(seconds=int(elapsed_time))), inline=True)
        embed.set_field_at(2, name="Resolutions found", value=str(resolution_count), inline=True)
        await message.edit(embed=embed)

    async def update_final_embed(self, message, domain, resolutions, use_csv, use_all, start_time):
        elapsed_time = time.time() - start_time
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        total_resolutions = len(resolutions)
        
        embed = discord.Embed(
            title="DNS Resolution Results",
            description=f"Retrieved DNS resolutions for **{domain}**",
            color=0x00FF00  # Green color
        )
        embed.add_field(name="Domain", value=domain, inline=False)
        embed.add_field(name="Total Resolutions", value=str(total_resolutions), inline=True)
        embed.add_field(name="Time taken", value=elapsed_str, inline=True)
        
        file_type = "CSV" if use_csv else "text"
        file = self.create_file(resolutions, domain, use_csv, use_all)
        
        embed.add_field(name="File Type", value=file_type, inline=True)
        
        await message.edit(embed=embed)
        await message.channel.send(f"Please find the complete list of DNS resolutions in the attached {file_type} file.", file=file)

    async def update_embed_on_failure(self, message, error_message):
        # Truncate the error message if it's too long
        max_error_length = 4000  # Leave some room for the embed title and other fields
        if len(error_message) > max_error_length:
            error_message = error_message[:max_error_length] + "... (truncated)"

        embed = discord.Embed(
            title="DNS Resolution Error",
            description=error_message,
            color=0xFF0000  # Red color
        )
        try:
            await message.edit(embed=embed)
        except discord.HTTPException as e:
            logger.error(f"Failed to update error embed: {str(e)}")
            # Fallback to a simple text message if embed fails
            await message.edit(content="An error occurred during DNS resolution. Please check the logs for details.")

    def create_file(self, resolutions, domain, use_csv, use_all):
        if use_csv:
            output = io.StringIO()
            writer = csv.writer(output)
            if use_all:
                writer.writerow(["Domain", "Subdomain", "Resolved Domain", "IP Address", "TTL", "Timestamp"])
                for item in resolutions:
                    if isinstance(item, dict):
                        writer.writerow([
                            domain,
                            item.get('subdomain', item.get('host', 'N/A')),
                            item.get('resolved_domain', item.get('host', 'N/A')),
                            item.get('ip_address', item.get('a', ['N/A'])[0] if item.get('a') else 'N/A'),
                            item.get('ttl', 'N/A'),
                            item.get('created_at', item.get('timestamp', 'N/A'))
                        ])
                    else:
                        # If item is not a dict, it's likely from !dns command
                        writer.writerow([domain, item, item, 'N/A', 'N/A', 'N/A'])
            else:
                writer.writerow(["Domain", "Subdomain", "Resolved Domain", "IP Address"])
                for item in resolutions:
                    if isinstance(item, dict):
                        writer.writerow([
                            domain,
                            item.get('subdomain', item.get('host', 'N/A')),
                            item.get('resolved_domain', item.get('host', 'N/A')),
                            item.get('ip_address', item.get('a', ['N/A'])[0] if item.get('a') else 'N/A')
                        ])
                    else:
                        # If item is not a dict, it's likely from !dns command
                        writer.writerow([domain, item, item, 'N/A'])
            output.seek(0)
            return discord.File(output, filename=f"{domain}_dns_resolutions.csv")
        else:
            # For text output, only include subdomain names
            file_content = "\n".join([
                item.get('subdomain', item.get('host', item)) if isinstance(item, dict) else item
                for item in resolutions
            ])
            return discord.File(io.StringIO(file_content), filename=f"{domain}_dns_resolutions.txt")

    async def create_all_resolutions_file(self, domain, use_csv):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{settings.API_URL}/api/v1/dns/subdomains-with-resolutions/{domain}') as response:
                if response.status == 200:
                    data = await response.json()
                    if use_csv:
                        output = io.StringIO()
                        writer = csv.writer(output)
                        writer.writerow(["Subdomain", "Resolved Domain", "Timestamp"])
                        for item in data:
                            writer.writerow([item['subdomain'], item['resolved_domain'], item['created_at']])
                        output.seek(0)
                        return discord.File(output, filename=f"{domain}_all_dns_resolutions.csv")
                    else:
                        file_content = "\n".join([f"{item['subdomain']},{item['resolved_domain']},{item['created_at']}" for item in data])
                        return discord.File(io.StringIO(file_content), filename=f"{domain}_all_dns_resolutions.txt")
                else:
                    logger.error(f"Failed to fetch all resolutions for {domain}: {response.status}")
                    return None

async def setup(bot):
    await bot.add_cog(DNSCog(bot))
    logger.info("DNSCog has been loaded")