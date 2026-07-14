from discord import Guild

from bridgewatcher.discord import bot
from bridgewatcher.discord.util.guild import ServerManager
from bridgewatcher.loggers import LOGGER


@bot.event
async def on_ready() -> None:
    LOGGER.info(f"Bot is ready and is serving for {len(bot.guilds)} servers")


@bot.event
async def on_guild_join(guild: Guild) -> None:
    LOGGER.info(f"Joined server {guild.name}")
    await ServerManager.get_or_create_conf(guild)


@bot.event
async def on_guild_remove(guild: Guild) -> None:
    LOGGER.info(f"Removed from server {guild.name}")
    await ServerManager.delete_conf(guild)
