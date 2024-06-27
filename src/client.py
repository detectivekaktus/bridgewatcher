#!/usr/bin/env python3
from asyncio import create_task
from datetime import datetime
from os import listdir
from typing import Final
from discord import Activity, ActivityType, Guild, Intents, Status
from discord.ext.commands import Bot
from src.api import AlbionOnlineDataManager
from src.config import Servers
from src.db import Database


INTENTS: Final[Intents] = Intents.default()
INTENTS.message_content = True
bot: Bot = Bot(command_prefix=";",
               intents=INTENTS,
               owner_id=692305905123065918,
               activity=Activity(type=ActivityType.listening, name="/help"),
               status=Status.do_not_disturb)
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
    await load_cogs()
    synched = await bot.tree.sync()
    
    print(f"Successfully logged as {bot.user} on {datetime.now().strftime("%d.%m.%Y %I:%M:%S %p")}.")
    print(f"Successfully synched {len(synched)} commands globally.")
    print(f"Running on {len(bot.guilds)} servers.")

    create_task(MANAGER.lifecycle())


@bot.event
async def on_guild_join(guild: Guild) -> None:
    SERVERS.create_config(guild)
