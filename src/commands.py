#!/usr/bin/env python3
from typing import Any
from discord.ext.commands import Context
from discord import Embed
import requests as req
from .client import bot
from .utils import convert_api_timestamp, get_percent_variation, notify_if_not_ok
from . import ERROR, GOLD


@bot.command()
async def gold(context: Context, num_entries: int = 4) -> None:
    if num_entries not in range(1, 25):
        await context.send(embed=Embed(title=":red_circle: The entries number is invalid!",
                                       color=ERROR,
                                       description="The number of entries must be between 1 and 24."))
        return

    try:
        response: req.Response = req.get(f"https://europe.albion-online-data.com/api/v2/stats/gold?count={num_entries + 1}", timeout=5)
        if await notify_if_not_ok(context, response): return
        data: Any = response.json()

        embed: Embed = Embed(title=f":coin: Gold prices",
                             color=GOLD,
                             description=f"Here are the past {num_entries} gold prices on the :flag_eu: European server.\n"
                             f"Total percent variation in the specified period: **{round((data[0]["price"] / data[-1]["price"] - 1) * 100, 2)}%**\n"
                             f"Total numeric variation in the specified period: **{(data[0]["price"] - data[-1]["price"])}**")

        for i in range(len(data) - 1):
            embed.add_field(name=f"Data from {convert_api_timestamp(data[i]["timestamp"])}.",
                            value=f"Gold price: **{data[i]["price"]}**\n"
                            f"Percent variation from the last value: **{get_percent_variation(data, i)}%**\n"
                            f"Numeric variation from the last value: **{data[i]["price"] - data[i + 1]["price"]}**")

        await context.send(embed=embed)
    except req.ReadTimeout:
        await context.send(embed=Embed(title=":red_circle: Request timed out :(",
                                       color=ERROR,
                                       description="I couldn't handle your request due to the long time it took to get the response.\n\n"
                                       "Try again later."))
