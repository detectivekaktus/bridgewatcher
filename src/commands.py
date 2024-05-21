#!/usr/bin/env python3
from typing import Any
from discord.ext.commands import BadArgument, Context
from discord import Embed
from requests import get, Response, ReadTimeout
from .client import bot
from .utils import convert_api_timestamp, get_percent_variation, notify_if_not_ok
from . import ERROR, GOLD, SUCCESS


@bot.command()
async def gold(context: Context, num_entries: int = 4) -> None:
    if num_entries not in range(1, 25):
        await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                       color=ERROR,
                                       description="Please, specify a valid integer value in range between 1 and 24."))
        return

    try:
        response: Response = get(f"https://europe.albion-online-data.com/api/v2/stats/gold?count={num_entries + 1}", timeout=5)
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
    except ReadTimeout:
        await context.send(embed=Embed(title=":red_circle: Request timed out :(",
                                       color=ERROR,
                                       description="I couldn't handle your request due to the long time it took to get the response.\n\n"
                                       "Try again later."))
        return


@gold.error
async def raise_error(context: Context, error: Any) -> None:
    if isinstance(error, BadArgument):
        await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                       color=ERROR,
                                       description="Please, specify a valid integer value in range between 1 and 24."))


@bot.hybrid_command()
async def help(context: Context) -> None:
    await context.send(embed=Embed(title=":wave: Hello!",
                                   color=SUCCESS,
                                   description="I'm Bridgewatcher, a discord bot created by <@692305905123065918> to simplify "
                                   "Albion Online crafting, refining and trading for the players that enjoy pieceful activities "
                                   "in the game.\n\n" "Currently I can **fetch gold prices** on the European server."))
