#!/usr/bin/env python3
from discord import Intents
from discord.ext.commands import Bot

from datetime import datetime

INTENTS: Intents = Intents.default()
INTENTS.message_content = True
bot: Bot = Bot(command_prefix="$", intents=INTENTS)


@bot.event
async def on_ready() -> None:
    print(f"Successfully logged as {bot.user} on {datetime.now().strftime("%d.%m.%Y %I:%M:%S %p")}.")
