from os import listdir
from typing import Final
from discord import Activity, ActivityType, Guild, Intents, Status
from discord.ext.commands import Bot
from bridgewatcher.api import AlbionOnlineDataManager
from bridgewatcher.server import ServerManager
from bridgewatcher.db import Database
from bridgewatcher.utils.annotations import overrides
from bridgewatcher.utils.logging import LOGGER


class Bridgewatcher(Bot):
    def __init__(self, intents: Intents) -> None:
        super().__init__(
            command_prefix=";",
            intents=intents,
            owner_id=692305905123065918,
            activity=Activity(type=ActivityType.listening, name="/help"),
            status=Status.do_not_disturb,
        )

    @overrides(Bot)
    async def setup_hook(self) -> None:
        LOGGER.info("Loading modules from `bridgewatcher.commands`.")
        await load_cogs()
        LOGGER.info(
            f"Successfully syncronized {len(await bot.tree.sync())} commands globally."
        )


INTENTS: Final[Intents] = Intents.default()
INTENTS.message_content = True
bot: Bridgewatcher = Bridgewatcher(INTENTS)
bot.remove_command("help")


DATABASE: Final[Database] = Database("/data/items.db")
SERVERS: Final[ServerManager] = ServerManager("/data/servers.db")
MANAGER: Final[AlbionOnlineDataManager] = AlbionOnlineDataManager()


async def load_cogs():
    for filename in listdir("src/bridgewatcher/commands"):
        if filename.endswith(".py"):
            await bot.load_extension(f"bridgewatcher.commands.{filename[:-3]}")


@bot.event
async def on_ready() -> None:
    LOGGER.info(f"Currently serving for {len(bot.guilds)} servers.")
    LOGGER.info("Bot instance is ready to handle requests.")


@bot.event
async def on_guild_join(guild: Guild) -> None:
    LOGGER.info(f"Joined guild {guild.name}.")
    SERVERS.create_config(guild)
