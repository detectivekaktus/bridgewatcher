#!/usr/bin/env python3
from datetime import datetime
from os import makedirs, path
from discord import Activity, ActivityType, Guild, Intents, Status
from discord.ext.commands import Bot

INTENTS: Intents = Intents.default()
INTENTS.message_content = True
bot: Bot = Bot(command_prefix=";",
               intents=INTENTS,
               activity=Activity(type=ActivityType.listening, name=";help"),
               status=Status.do_not_disturb)
bot.remove_command("help")


def create_server_config(guild: Guild) -> None:
    if not path.exists("servers/"):
        makedirs("servers/")
    write_config(guild, 1)


def update_server_config(guild: Guild, fetch_server: int) -> None:
    if not has_config(guild):
        create_server_config(guild)
        return
    write_config(guild, fetch_server)


def write_config(guild: Guild, fetch_server: int) -> None:
    with open(f"servers/{guild.id}.json", "w") as config:
        config.write("{\n")
        config.write(f"  \"name\": \"{guild.name}\",\n")
        config.write(f"  \"owner_id\": {guild.owner_id},\n")
        config.write(f"  \"fetch_server\": {fetch_server}\n")
        config.write("}\n")


def has_config(guild: Guild) -> bool:
    if not path.exists(f"servers/{guild.id}.json"): return False
    return True


@bot.event
async def on_ready() -> None:
    print(f"Successfully logged as {bot.user} on {datetime.now().strftime("%d.%m.%Y %I:%M:%S %p")}.")


@bot.event
async def on_guild_join(guild: Guild) -> None:
    create_server_config(guild)
