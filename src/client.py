#!/usr/bin/env python3
from datetime import datetime
from typing import Literal, Optional
from discord import Activity, ActivityType, Guild, HTTPException, Intents, Object, Status
from discord.ext.commands import Bot, Context, Greedy, guild_only, is_owner
from src.commands.calcs import CalcsCog
from src.commands.info import InfoCog
from src.commands.settings import SettingsCog
from src.config.config import create_server_config


INTENTS: Intents = Intents.default()
INTENTS.message_content = True
bot: Bot = Bot(command_prefix=";",
               intents=INTENTS,
               owner_id = 692305905123065918,
               activity=Activity(type=ActivityType.listening, name=";help"),
               status=Status.do_not_disturb)
bot.remove_command("help")


@bot.command()
@guild_only()
@is_owner()
async def sync(context: Context, guilds: Greedy[Object], spec: Optional[Literal["~", "*"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await bot.tree.sync(guild=context.guild)
            await context.send(f"Successfully synchronized {len(synced)} commands in the current server.")
            return
        elif spec == "*":
            synced = await bot.tree.sync()
            await context.send(f"Successfully synchronized {len(synced)} commands globally.")
            return
        elif spec != None:
            await context.send(f"Unknown spec {spec}. No commands synchronized.")
            return

    synced = 0
    for guild in guilds:
        try:
            await bot.tree.sync(guild=guild)
        except HTTPException: pass
        else:
           synced += 1
    await context.send(f"Successfully synchronized {synced} commands in {len(guilds)} servers.")


async def setup_bot(bot: Bot) -> None:
    await bot.add_cog(InfoCog(bot))
    await bot.add_cog(SettingsCog(bot))
    await bot.add_cog(CalcsCog(bot))


@bot.event
async def on_ready() -> None:
    print(f"Successfully logged as {bot.user} on {datetime.now().strftime("%d.%m.%Y %I:%M:%S %p")}.")


@bot.event
async def on_guild_join(guild: Guild) -> None:
    create_server_config(guild)
