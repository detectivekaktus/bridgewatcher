from os import listdir
from typing import override

from discord import Intents
from discord.ext.commands import Bot

from bridgewatcher.db.seed.run import seed_if_needed
from bridgewatcher.loggers import LOGGER


class Bridgewatcher(Bot):
    def __init__(self, intents: Intents) -> None:
        super().__init__("?", intents=intents)

    async def _load_cogs(self) -> None:
        for filename in listdir("src/bridgewatcher/discord/cogs"):
            if filename == "__init__.py" or not filename.endswith(".py"):
                continue
            await self.load_extension(f"bridgewatcher.discord.cogs.{filename[:-3]}")

    @override
    async def setup_hook(self) -> None:
        LOGGER.info("Running seeding checks...")
        await seed_if_needed()

        LOGGER.info("Loading commands from cogs...")
        await self._load_cogs()

        self.remove_command("help")

        LOGGER.info("Synchronizing commands with Discord...")
        commands = len(await self.tree.sync())
        LOGGER.info(f"Successfully synchronized {commands} commands with Discord")

        LOGGER.info(f"Ready for {self.guilds} servers")


intents = Intents.default()
intents.message_content = True
bot = Bridgewatcher(intents)

DETECTIVEKAKTUS_ID = 692305905123065918

__all__ = ("bot", "DETECTIVEKAKTUS_ID")
