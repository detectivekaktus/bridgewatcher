#!/usr/bin/env python3
from typing import Any, List, Optional, cast
from discord import Embed, Guild, Interaction
from discord.app_commands import command, describe
from discord.ext.commands import Bot, Cog, guild_only
from src.api import AODFetcher, ItemManager, SBIRenderFetcher, convert_api_timestamp, get_percent_variation, strquality_toint
from src.components.ui import PriceView
from src.config.config import get_server_config
from src import ERROR_COLOR, GOLD_COLOR, PRICE_COLOR


class InfoCog(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command(name="gold", description="Retieves gold prices.")
    @describe(count="Number of past gold prices.")
    @guild_only()
    async def gold(self, interaction: Interaction, count: int = 3) -> None:
        if count not in range(1, 25):
            await interaction.response.send_message(embed=Embed(title=":red_circle: Invalid argument!",
                                                                color=ERROR_COLOR,
                                                                description="Please, specify a valid integer value in "
                                                                "range between 1 and 24."))
            return

        cfg: dict[str, Any] = get_server_config(cast(Guild, interaction.guild))
        fetcher: AODFetcher = AODFetcher(cfg["fetch_server"])
        data: Optional[List[dict[str, Any]]] = fetcher.fetch_gold(count + 1)
        if not data:
            await interaction.response.send_message(embed=Embed(title=":red_circle: There was an error",
                                                                color=ERROR_COLOR,
                                                                description="I've encountered an error trying to get item "
                                                                "prices from the API. Please, try again later."))
            return

        embed: Embed = Embed(title=":coin: Gold prices",
                             color=GOLD_COLOR,
                             description=f"Here are the past {count} gold prices.\n"
                             "Total percent variation in the specified period: "
                             f"**{round((data[0]["price"] / data[-1]["price"] - 1) * 100, 2):,}%**\n"
                             "Total numeric variation in the specified period: "
                             f"**{(data[0]["price"] - data[-1]["price"]):,}**")
        embed.set_footer(text="The data is provided by the Albion Online Data Project\n")

        for i in range(len(data) - 1):
            embed.add_field(name=f"Data from {convert_api_timestamp(data[i]["timestamp"])}.",
                            value=f"Gold price: **{data[i]["price"]}**\n"
                            f"Percent variation from the last value: **{get_percent_variation(data, i)}%**\n"
                            f"Numeric variation from the last value: **{data[i]["price"] - data[i + 1]["price"]}**")

        await interaction.response.send_message(embed=embed)


    @command(name="price", description="Retrieves price of an item.")
    @describe(item_name="The Albion Online Data Project API item name.")
    @guild_only()
    async def price(self, interaction: Interaction, item_name: str) -> None:
        item_name = item_name.upper()

        if not ItemManager.exists(item_name):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name} doesn't exist!",
                                                          color=ERROR_COLOR,
                                                          description=f"{item_name} is not an existing item!"))
            return

        view = PriceView(timeout=60)
        await interaction.response.send_message(embed=Embed(title="Price fetcher",
                                                            color=PRICE_COLOR,
                                                            description="Welcome to an updated version of the price"
                                                            " fetcher component of Bridgewatcher! Here you can modify"
                                                            " the data you want to fetch.\n\n"
                                                            "Use `quality` button to select the quality of the item."
                                                            " The default value if not specified is 1.\n\n"
                                                            "Use `cities` button to select the cities from which you"
                                                            " want to know the price. If not specified, gives informa"
                                                            "tion from all the in-game cities."),
                                                view=view,
                                                ephemeral=True)
        if not await view.wait():
            message = await interaction.original_response()
            await message.delete()

            quality: int = strquality_toint(view.quality)

            fetcher: AODFetcher = AODFetcher(get_server_config(cast(Guild, interaction.guild))["fetch_server"])
            data: Optional[List[dict[str, Any]]] = fetcher.fetch_price(item_name, quality, cast(List[str], view.cities))
            if not data:
                await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                            color=ERROR_COLOR,
                                                            description="I couldn't handle you request due to "
                                                            "a server problem. Try again later."),
                                                ephemeral=True)

                return

            embed: Embed = Embed(title=f"{data[0]["item_id"]} price",
                                 color=PRICE_COLOR,
                                 description=f"Here are the prices of {data[0]["item_id"]} in different "
                                 "cities. You can find the full list of item [here](https://github.com/"
                                 "ao-data/ao-bin-dumps/blob/master/formatted/items.txt).")
            embed.set_thumbnail(url=SBIRenderFetcher.fetch_item(item_name, quality))
            embed.set_footer(text="The data is provided by the Albion Online Data Project.")

            for entry in data:
                embed.add_field(name=f"{entry["city"]}",
                                value=f"Updated at: **{convert_api_timestamp(entry["sell_price_min_date"])}** "
                                f"and **{convert_api_timestamp(entry["buy_price_max_date"])}**\n"
                                f"Sold at: **{entry["sell_price_min"]:,}**\n"
                                f"Bought at: **{entry["buy_price_max"]:,}**")
            await interaction.followup.send(embed=embed)
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=Embed(title=":red_circle: Timed out!",
                                                        color=ERROR_COLOR,
                                                        description="Your time has run out. Start a new "
                                                        "conversation with the bot to get the price."),
                                            ephemeral=True)
