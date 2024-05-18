#!/usr/bin/env python3
from . import ERROR, GOLD
from .client import bot
from discord import Embed
from discord.ext.commands import Context
from datetime import datetime
import requests as req

@bot.command()
async def gold(context: Context, entries: int = 4) -> None:
    if entries not in range(1, 26):
        await context.send(embed=Embed(title=":red_circle: The entries number is invalid!",
                                       color=ERROR,
                                       description="The number of entries must be between 1 and 25."))
        return

    try:
        res: req.Response = req.get(f"https://europe.albion-online-data.com/api/v2/stats/gold?count={entries}", timeout=5)
        if not res.ok:
            await context.send(embed=Embed(title=":red_circle: Your request cannot be processed!",
                                           color=ERROR,
                                           description="The input you provided is invalid and cannot be processed correctly by the system. Please, make a resonable request."))
            return

        embed: Embed = Embed(title=f":coin: Gold prices",
                             color=GOLD,
                             description=f"Here you have your {entries} gold prices on the :flag_eu: European server.")
        for entry in res.json():
            embed.add_field(name=f"Price on {datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:00:00").strftime("%d.%m.%Y %I %p UTC")}",
                            value=f"${entry["price"]}")

        await context.send(embed=embed)
    except req.ReadTimeout:
        await context.send(embed=Embed(title=":red_circle: Request timed out :(",
                                       color=ERROR,
                                       description="I couldn't handle your request due to the long time it took to get the response.\n\nTry again later."))
