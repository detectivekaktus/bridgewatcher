#!/usr/bin/env python3
from datetime import datetime
from discord import Activity, ActivityType, Intents, Status
from discord.ext.commands import Bot

INTENTS: Intents = Intents.default()
INTENTS.message_content = True
bot: Bot = Bot(command_prefix=";",
               intents=INTENTS,
               activity=Activity(type=ActivityType.listening, name=";help"),
               status=Status.do_not_disturb)
bot.remove_command("help")


@bot.event
async def on_ready() -> None:
    print(f"Successfully logged as {bot.user} on {datetime.now().strftime("%d.%m.%Y %I:%M:%S %p")}.")
