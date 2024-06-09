#!/usr/bin/env python3
from datetime import datetime
from discord import Activity, ActivityType, Guild, Intents, Status
from discord.ext.commands import Bot
from src.commands.calcs import CalcsCog
from src.commands.error_handler import CommandErrorHandler
from src.commands.info import InfoCog
from src.commands.settings import SettingsCog
from src.config.config import create_server_config


INTENTS: Intents = Intents.default()
INTENTS.message_content = True
bot: Bot = Bot(command_prefix=";",
               intents=INTENTS,
               owner_id=692305905123065918,
               activity=Activity(type=ActivityType.listening, name=";help"),
               status=Status.do_not_disturb)
bot.remove_command("help")


async def setup_bot(bot: Bot) -> None:
    await bot.add_cog(CommandErrorHandler(bot))
    await bot.add_cog(InfoCog(bot))
    await bot.add_cog(SettingsCog(bot))
    await bot.add_cog(CalcsCog(bot))


@bot.event
async def on_ready() -> None:
    print(f"Successfully logged as {bot.user} on {datetime.now().strftime("%d.%m.%Y %I:%M:%S %p")}.")

    synched = await bot.tree.sync()
    print(f"Successfully synched {len(synched)} commands globally.")



@bot.event
async def on_guild_join(guild: Guild) -> None:
    create_server_config(guild)
