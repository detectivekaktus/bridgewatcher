#!/usr/bin/env python3
from .client import bot

from discord import Embed
from discord.ext.commands import Context

from datetime import datetime

import requests as req

@bot.command()
async def gold(context: Context, entries: int = 4) -> None:
    try:
        res: req.Response = req.get(f"https://europe.albion-online-data.com/api/v2/stats/gold?count={entries}", timeout=5)
        embed: Embed = Embed(title=f":coin: Gold prices", color=0xf5d62a, description=f"Here you have your {entries} gold prices on the :flag_eu: European server.\n")
        for entry in res.json():
            embed.add_field(name=f"Price on {datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:00:00").strftime("%d.%m.%Y %I %p UTC")}", value=f"${entry["price"]}")
        await context.send(embed=embed)
    except req.ReadTimeout:
        await context.send(embed=Embed(title=":red_circle: Request timed out :(", color=0xff1231, description="I couldn't handle your request due to the long time it took to get the response.\n\nTry again later."))
