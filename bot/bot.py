# bot/bot.py

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from app.core.logging_config import setup_logging

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Setup logging
setup_logging()
logger = logging.getLogger("bbrf_discord_bot")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is connected to {len(bot.guilds)} guilds')

    for filename in os.listdir('./bot/cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'bot.cogs.{filename[:-3]}')
                logger.info(f'Loaded extension: {filename[:-3]}')
            except Exception as e:
                logger.error(f'Failed to load extension {filename[:-3]}: {str(e)}', exc_info=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logger.warning(f'Command not found: {ctx.message.content}')
        await ctx.send("Command not found. Type !help for a list of available commands.")
    else:
        logger.error(f"Error executing command '{ctx.command}': {str(error)}", exc_info=True)
        await ctx.send(f"An error occurred while executing the command: {str(error)}")

@bot.event
async def on_guild_join(guild):
    logger.info(f'Bot has joined a new guild: {guild.name} (id: {guild.id})')

@bot.event
async def on_guild_remove(guild):
    logger.info(f'Bot has been removed from a guild: {guild.name} (id: {guild.id})')

def run_bot():
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Failed to start the bot: {str(e)}", exc_info=True)

if __name__ == "__main__":
    run_bot()