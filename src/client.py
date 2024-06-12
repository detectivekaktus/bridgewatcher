#!/usr/bin/env python3
from datetime import datetime
from os import listdir
from discord import Activity, ActivityType, Guild, Intents, Status
from discord.ext.commands import Bot
from src.config.config import Servers
from src.db.database import Database


INTENTS: Intents = Intents.default()
INTENTS.message_content = True
bot: Bot = Bot(command_prefix=";",
               intents=INTENTS,
               owner_id=692305905123065918,
               activity=Activity(type=ActivityType.listening, name=";help"),
               status=Status.do_not_disturb)
bot.remove_command("help")

database: Database = Database("res/items.db")
servers: Servers = Servers("servers/servers.db")


async def load_cogs():
    for filename in listdir("src/commands"):
        if filename.endswith(".py"):
            await bot.load_extension(f"src.commands.{filename[:-3]}")

@bot.event
async def on_ready() -> None:
    print(f"Successfully logged as {bot.user} on {datetime.now().strftime("%d.%m.%Y %I:%M:%S %p")}.")
    await load_cogs()
    synched = await bot.tree.sync()
    print(f"Successfully synched {len(synched)} commands globally.")



@bot.event
async def on_guild_join(guild: Guild) -> None:
    servers.create_config(guild)
