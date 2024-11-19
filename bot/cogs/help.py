import discord
from discord.ext import commands
import logging

logger = logging.getLogger("bbrf_discord_bot")

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def bbrf_help(self, ctx):
        """Display help information for BBRF commands"""
        embed = discord.Embed(
            title="Welcome to ReconThing",
            description="Here are the available commands for each module:",
            color=discord.Color.blue()
        )

        # Basic Recon
        embed.add_field(
            name="Basic Recon",
            value="`!basicrecon domain.ltd` - Run a comprehensive recon on the specified domain",
            inline=False
        )

        # Subdomain Enumeration
        embed.add_field(
            name="Subdomain Enumeration",
            value=(
                "• `!subdomain domain.ltd` - Enumerate subdomains\n"
                "• `!getsubdomain domain.ltd` - Retrieve subdomain results\n"
                "• Supported flags: `-csv` (get file with csv format results)"
            ),
            inline=False
        )

        # DNS Resolving
        embed.add_field(
            name="DNS Resolving",
            value=(
                "• `!dns domain.ltd` - Perform DNS resolution\n"
                "• `!getdns domain.ltd` - Retrieve DNS results\n"
                "• Supported flags: `-csv` (get file with csv format results with IP information included)"
            ),
            inline=False
        )

        # HTTP Probing
        embed.add_field(
            name="HTTP Probing",
            value=(
                "• `!http domain.ltd` - Probe HTTP endpoints\n"
                "• `!gethttp domain.ltd` - Retrieve HTTP probing results\n"
                "• Supported flags: `-csv` (get file with csv format results with IP, webserver, technology, status code information included)"
            ),
            inline=False
        )


        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
    logger.info("HelpCog has been loaded")
