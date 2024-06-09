#!/usr/bin/env python3
from typing import Any, List, Optional, cast
from discord import ButtonStyle, Embed, Guild, Interaction
from discord.app_commands import command, describe
from discord.ext.commands import BadArgument, Bot, Cog, guild_only
from discord.ui import Button, Modal, TextInput, View, button
from src.api import AODFetcher, ItemManager, SBIRenderFetcher, are_valid_cities, convert_api_timestamp, get_percent_variation, parse_cities
from src.config.config import get_server_config
from src import ERROR_COLOR, GOLD_COLOR, PRICE_COLOR


class PriceView(View):
    def __init__(self, *, timeout: Optional[float] = 180) -> None:
        super().__init__(timeout=timeout)
        self.quality: int = 1
        self.cities: List[str] = []


    @button(label="Quality", style=ButtonStyle.gray)
    async def quality_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(QualityModal(self))

    @button(label="Cities", style=ButtonStyle.gray)
    async def cities_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(CitiesModal(self))

    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self.stop()


class QualityModal(Modal):
    def __init__(self, view: PriceView, *, title: str = "Quality", timeout: Optional[float] = None, custom_id: str = "qualmod") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.view: PriceView = view
        self.quality: TextInput = TextInput(label=title, placeholder="Enter a number from 1 to 5 here")
        self.add_item(self.quality)

    async def on_submit(self, interaction: Interaction) -> None:
        try:
            quality = int(self.quality.value)
            if quality not in range(1, 6):
                raise ValueError(f"{quality} is not in range from 1 to 5.")
            self.view.quality = quality
            await interaction.response.defer()
        except:
            await interaction.response.send_message(f"{self.quality.value} is not valid integer from 1 to 5.\n\n",
                                                    ephemeral=True,
                                                    delete_after=5)


class CitiesModal(Modal):
    def __init__(self, view: PriceView, *, title: str = "Cities", timeout: Optional[float] = None, custom_id: str = "citmod") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.view: PriceView = view
        self.cities: TextInput = TextInput(label=title, placeholder="Enter a city here")
        self.add_item(self.cities)

    async def on_submit(self, interaction: Interaction) -> None:
        cities: List[str] = parse_cities(self.cities.value)
        if not are_valid_cities(cities):
            await interaction.response.send_message(f"Some city doesn't appear to be a valid city.\n\n",
                                                    ephemeral=True,
                                                    delete_after=5)
            return
        self.view.cities = cities
        await interaction.response.defer()


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

            fetcher: AODFetcher = AODFetcher(get_server_config(cast(Guild, interaction.guild))["fetch_server"])
            data: Optional[List[dict[str, Any]]] = fetcher.fetch_price(item_name, view.quality, cast(List[str], view.cities))
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
            embed.set_thumbnail(url=SBIRenderFetcher.fetch_item(item_name, view.quality))
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
