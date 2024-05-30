#!/usr/bin/env python3
from typing import Any, List, cast
from discord import Embed
from discord.ext.commands import BadArgument, Bot, Cog, Context, command, guild_only, hybrid_command
from src.api import AODFetcher, SBIRenderFetcher, convert_api_timestamp, get_percent_variation, is_valid_city
from src.config.config import get_server_config
from src import ERROR, GOLD, PRICE


class InfoCog(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @hybrid_command()
    @guild_only()
    async def gold(self, context: Context, count: int = 3) -> None:
        if not context.guild:
            await context.send(embed=Embed(title=":red_circle: Fatal error!",
                                           color=ERROR,
                                           description="This command can be invoked only on a server!"))
            return
    
        if count not in range(1, 25):
            await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                           color=ERROR,
                                           description="Please, specify a valid integer value in "
                                           "range between 1 and 24."))
            return
        
        cfg: dict[str, Any] = get_server_config(context.guild)
        fetcher: AODFetcher = AODFetcher(cast(int, cfg.get("fetch_server")))
        data: List[dict[str, Any]] | None = fetcher.fetch_gold(count + 1)
        if not data:
            await context.send(embed=Embed(title=":red_circle: There was an error",
                                           color=ERROR,
                                           description="I've encountered an error trying to get item "
                                           "prices from the API. Please, try again later."))
            return
    
        embed: Embed = Embed(title=":coin: Gold prices",
                             color=GOLD,
                             description=f"Here are the past {count} gold prices.\n"
                             "Total percent variation in the specified period: "
                             f"**{round((data[0]["price"] / data[-1]["price"] - 1) * 100, 2)}%**\n"
                             "Total numeric variation in the specified period: "
                             f"**{(data[0]["price"] - data[-1]["price"])}**")
        embed.set_footer(text="The data is provided by the Albion Online Data Project\n")
    
        for i in range(len(data) - 1):
            embed.add_field(name=f"Data from {convert_api_timestamp(data[i]["timestamp"])}.",
                            value=f"Gold price: **{data[i]["price"]}**\n"
                            f"Percent variation from the last value: **{get_percent_variation(data, i)}%**\n"
                            f"Numeric variation from the last value: **{data[i]["price"] - data[i + 1]["price"]}**")
    
        await context.send(embed=embed)
    
    @gold.error
    async def raise_gold_error(self, context: Context, error: Any) -> None:
        if isinstance(error, BadArgument):
            await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                           color=ERROR,
                                           description="Please, specify a valid integer value in range "
                                           "between 1 and 24."))
    

    @command()
    @guild_only()
    async def price(self, context: Context, item_name: str, *args: str) -> None:
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
                                                   description="Please, specify a valid integer value "
                                                   "in range between 1 and 5 for `quality`."))
                    return
            else:
                if not is_valid_city(arg):
                    await context.send(embed=Embed(title=":red_cirlce: Invalid argument!",
                                                   color=ERROR,
                                                   description=f"{arg} doesn't appear to be a valid city "
                                                   "to ask prices from."))
                    return
                cities.append(arg)
        
        cfg: dict[str, Any] = get_server_config(context.guild)
        fetcher: AODFetcher = AODFetcher(cast(int, cfg.get("fetch_server")))
        image_render: SBIRenderFetcher = SBIRenderFetcher()
        data: List[dict[str, Any]] | None = fetcher.fetch_price(item_name, quality, cities)
        if not data:
            await context.send(embed=Embed(title=":red_cirlce: There was an error",
                                           color=ERROR,
                                           description="I've encountered an error trying to get gold "
                                           "prices from the API. Please, try again later."))
            return
        
        embed: Embed = Embed(title=f"{data[0]["item_id"]} price.",
                             color=PRICE,
                             description=f"Here are the price of {data[0]["item_id"]} in different "
                             "cities. You can find the full list of items [here](https://github.com/"
                             "ao-data/ao-bin-dumps/blob/master/formatted/items.txt).")
        embed.set_thumbnail(url=image_render.fetch_item(item_name, quality))
        embed.set_footer(text="The data is provided by the Albion Online Data Project\n")
    
        for entry in data:
            embed.add_field(name=f"{entry["city"]}",
                            value=f"Updated at: **{convert_api_timestamp(entry["sell_price_min_date"])}**"
                            f" and **{convert_api_timestamp(entry["buy_price_max_date"])}**\n"
                            f"Sold at: **{entry["sell_price_min"]}**\n"
                            f"Bought at: **{entry["buy_price_max"]}**")
        await context.send(embed=embed)
    
    
    @price.error
    async def raise_price_error(self, context: Context, error: Any) -> None:
        if isinstance(error, BadArgument):
            await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                           color=ERROR,
                                           description="Please, specify valid `item_name` and `quality` "
                                           "for the item you want to find.\n"
                                           "You can find the list of items [here](https://github.com/ao-"
                                           "data/ao-bin-dumps/blob/master/formatted/items.txt)."))
