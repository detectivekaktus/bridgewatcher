#!/usr/bin/env python3
from json import load
from typing import Any, List
from discord.ext.commands import BadArgument, Context
from discord import Embed
from .api import AODFetcher, SBIRenderFetcher, get_percent_variation, convert_api_timestamp, is_valid_city
from .client import bot, create_server_config, has_config, update_server_config
from . import ERROR, GOLD, PRICE, SUCCESS


@bot.command()
async def gold(context: Context, count: int = 3) -> None:
    if not context.guild:
        await context.send(embed=Embed(title=":red_circle: Fatal error!",
                                       color=ERROR,
                                       description="This command can be invoked only on a server!"))
        return

    if count not in range(1, 25):
        await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                       color=ERROR,
                                       description="Please, specify a valid integer value in range between 1 and 24."))
        return
    
    if not has_config(context.guild):
        create_server_config(context.guild)

    with open(f"servers/{context.guild.id}.json", "r") as f:
        cfg = load(f)

    fetcher: AODFetcher = AODFetcher(cfg.get("fetch_server"))
    data: List[dict[str, Any]] | None = fetcher.fetch_gold(count + 1)
    if not data:
        await context.send(embed=Embed(title=":red_circle: There was an error",
                                       color=ERROR,
                                       description="I've encountered an error trying to get item prices from the API. Please, try again later."))
        return

    embed: Embed = Embed(title=":coin: Gold prices",
                         color=GOLD,
                         description=f"Here are the past {count} gold prices.\n"
                         f"Total percent variation in the specified period: **{round((data[0]["price"] / data[-1]["price"] - 1) * 100, 2)}%**\n"
                         f"Total numeric variation in the specified period: **{(data[0]["price"] - data[-1]["price"])}**")
    embed.set_footer(text="The data is provided by the Albion Online Data Project\n")

    for i in range(len(data) - 1):
        embed.add_field(name=f"Data from {convert_api_timestamp(data[i]["timestamp"])}.",
                        value=f"Gold price: **{data[i]["price"]}**\n"
                        f"Percent variation from the last value: **{get_percent_variation(data, i)}%**\n"
                        f"Numeric variation from the last value: **{data[i]["price"] - data[i + 1]["price"]}**")

    await context.send(embed=embed)


@gold.error
async def raise_gold_error(context: Context, error: Any) -> None:
    if isinstance(error, BadArgument):
        await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                       color=ERROR,
                                       description="Please, specify a valid integer value in range between 1 and 24."))


@bot.command()
async def price(context: Context, item_name: str, *args: str) -> None:
    if not context.guild:
        await context.send(embed=Embed(title=":red_circle: Fatal error!",
                                       color=ERROR,
                                       description="This command can be invoked only on a server!"))
        return

    quality: int = 1
    cities: List[str] = []

    for arg in args:
        if arg.isdigit():
            quality = int(arg)
            if quality not in range(1, 6):
                await context.send(embed=Embed(title=":red_cicle: Invalid argument!",
                                               color=ERROR,
                                               description="Please, specify a valid integer value in range between 1 and 5 for `quality`."))
                return
        else:
            cities.append(arg)

    for city in cities:
        if not is_valid_city(city):
            await context.send(embed=Embed(title=":red_cirlce: Invalid argument!",
                                           color=ERROR,
                                           description=f"{city} doesn't appear to be a valid city to ask prices from."))
            return
    
    if not has_config(context.guild):
        create_server_config(context.guild)

    with open(f"servers/{context.guild.id}.json", "r") as f:
        cfg = load(f)

    fetcher: AODFetcher = AODFetcher(cfg.get("fetch_server"))
    image_render: SBIRenderFetcher = SBIRenderFetcher()
    data: List[dict[str, Any]] | None = fetcher.fetch_price(item_name, quality, cities)
    if not data:
        await context.send(embed=Embed(title=":red_cirlce: There was an error",
                                       color=ERROR,
                                       description="I've encountered an error trying to get gold prices from the API. Please, try again later."))
        return
    
    embed: Embed = Embed(title=f"{data[0]["item_id"]} price.",
                         color=PRICE,
                         description=f"Here are the price of {data[0]["item_id"]} in different cities on the :flag_eu: "
                         "European server. You can find the full list of items [here](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.txt).")
    embed.set_thumbnail(url=image_render.fetch_item(item_name, quality))
    embed.set_footer(text="The data is provided by the Albion Online Data Project\n")

    for entry in data:
        embed.add_field(name=f"{entry["city"]}",
                        value=f"Updated at: **{convert_api_timestamp(entry["sell_price_min_date"])}** and **{convert_api_timestamp(entry["buy_price_max_date"])}**\n"
                        f"Sold at: **{entry["sell_price_min"]}**\n"
                        f"Bought at: **{entry["buy_price_max"]}**")
    await context.send(embed=embed)


@price.error
async def raise_price_error(context: Context, error: Any) -> None:
    if isinstance(error, BadArgument):
        await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                       color=ERROR,
                                       description="Please, specify valid `item_name` and `quality` for the item you want to find.\n"
                                       "You can find the list of items [here](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.txt)."))


@bot.command()
async def set_server(context: Context, server: int) -> None:
    if not context.guild:
        await context.send(embed=Embed(title=":red_circle: Fatal error!",
                                       color=ERROR,
                                       description="This command can be invoked only on a server!"))
        return

    if server not in range(1, 4):
        await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                       color=ERROR,
                                       description="Please, specify a valid integer value in range from 1 to 3 for `server` argument."))
        return

    if not has_config(context.guild):
        create_server_config(context.guild)

    update_server_config(context.guild, server)
    match server:
        case 1:
            await context.send("Server successfully changed to :flag_us: America.")
        case 2:
            await context.send("Server successfully changed to :flag_eu: Europe.")
        case 3:
            await context.send("Server successfully changed to :flag_cn: Asia.")


@set_server.error
async def raise_set_server_error(context: Context, error: Any) -> None:
    if isinstance(error, BadArgument):
        await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                       color=ERROR,
                                       description="Please, specify a valid integer value in range from 1 to 3 for `server` argument."))


@bot.command()
async def help(context: Context) -> None:
    if not context.guild:
        await context.send(embed=Embed(title=":red_circle: Fatal error!",
                                       color=ERROR,
                                       description="This command can be invoked only on a server!"))
        return

    with open(f"servers/{context.guild.id}.json", "r") as f:
        cfg = load(f)

    embed = Embed(title=":wave: Hello!",
                                   color=SUCCESS,
                                   description="I'm Bridgewatcher, a discord bot created by <@692305905123065918> to simplify "
                                   "Albion Online crafting, refining and trading for the players that enjoy pieceful activities "
                                   "in the game.\n\n" "Use `;gold <hours>` to check the gold price and its changements on the European "
                                   "server. You can check up to 24 prices at once. The default number of prices fetched is 3.\n\n"
                                   "Use `;price <item_name> <quality> <cities>` to check the item price in all the in-game markets"
                                   "(black market included).\n\n" "This project is made thanks to the Albion Online Data Project "
                                   "which provides the bot with all the necessary data. If you want to help this project, install "
                                   "the [Albion Online Data Project client](https://albion-online-data.com/).")
    embed.set_author(name="Made by DetectiveKaktus", url="https://github.com/detectivekaktus")
    match cfg.get("fetch_server"):
        case 1:
            embed.add_field(name="Currently fetching on :flag_us: American server", value="")
        case 2:
            embed.add_field(name="Currently fetching on :flag_eu: European server", value="")
        case 3:
            embed.add_field(name="Currently fetching on :flag_cn: Asian server", value="")
    await context.send(embed=embed)
