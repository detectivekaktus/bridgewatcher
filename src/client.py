#!/usr/bin/env python3
from os import listdir
from typing import Final
from discord import Activity, ActivityType, Guild, Intents, Status
from discord.ext.commands import Bot
from src.api import AlbionOnlineDataManager
from src.config import Servers
from src.db import Database
from src.utils.annotations import overrides
from src.utils.logging import LOGGER


class Bridgewatcher(Bot):
    def __init__(self, intents: Intents) -> None:
        super().__init__(command_prefix=';',
                         intents=intents,
                         owner_id=692305905123065918,
                         activity=Activity(type=ActivityType.listening, name="/help"),
                         status=Status.do_not_disturb)


    @overrides(Bot)
    async def setup_hook(self) -> None:
        LOGGER.info("Loading modules from `src.commands`.")
        await load_cogs()
        LOGGER.info(f"Successfully syncronized {len(await bot.tree.sync())} commands globally.")
        LOGGER.info("Creating separate task for cache manager.")
        self.loop.create_task(MANAGER.lifecycle())


INTENTS: Final[Intents] = Intents.default()
INTENTS.message_content = True
bot: Bridgewatcher = Bridgewatcher(INTENTS)
bot.remove_command("help")


DATABASE: Final[Database] = Database("res/items.db")
SERVERS: Final[Servers] = Servers("servers/servers.db")
MANAGER: Final[AlbionOnlineDataManager] = AlbionOnlineDataManager(DATABASE)


async def load_cogs():
    for filename in listdir("src/commands"):
        if filename.endswith(".py"):
            await bot.load_extension(f"src.commands.{filename[:-3]}")


@bot.event
async def on_ready() -> None:
    LOGGER.info(f"Currently serving for {len(bot.guilds)} servers.")
    LOGGER.info("Bot instance is ready to handle requests.")


@bot.event
async def on_guild_join(guild: Guild) -> None:
    LOGGER.info(f"Joined guild {guild.name}.")
    SERVERS.create_config(guild)
