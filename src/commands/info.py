#!/usr/bin/env python3
from typing import Any, List, Optional, cast
from discord import ButtonStyle, Embed, Guild, Interaction
from discord.app_commands import command, describe
from discord.ext.commands import BadArgument, Bot, Cog, guild_only
from discord.ui import Button, Modal, TextInput, View, button
from src.api import AODFetcher, SBIRenderFetcher, convert_api_timestamp, get_percent_variation, is_valid_city, parse_cities
from src.config.config import get_server_config
from src import ERROR, GOLD, PRICE


class PriceView(View):
    def __init__(self, *, timeout: Optional[float] = 180) -> None:
        super().__init__(timeout=timeout)
        self.quality_modal = QualityModal()
        self.cities_modal = CitiesModal()


    @button(label="Quality", style=ButtonStyle.blurple)
    async def quality_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(self.quality_modal)

    @button(label="Cities", style=ButtonStyle.gray)
    async def cities_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(self.cities_modal)

    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_message("Processing...", ephemeral=True)
        self.stop()


class QualityModal(Modal):
    def __init__(self, *, title: str = "Quality", timeout: Optional[float] = None, custom_id: str = "qualmod") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.quality = TextInput(label="Quality", placeholder="Enter a number from 1 to 5 here")
        self.add_item(self.quality)

    async def on_submit(self, interaction: Interaction) -> None:
        try:
            quality = int(self.quality.value)
            await interaction.response.send_message(f"Successfully added {quality} as the quality parameter.",
                                                    ephemeral=True)
            self.stop()
        except:
            await interaction.response.send_message(f"{self.quality.value} is not valid integer from 1 to 5.\n\n"
                                                    "Start a new conversation with the bot.",
                                                    ephemeral=True)


class CitiesModal(Modal):
    def __init__(self, *, title: str = "Cities", timeout: Optional[float] = None, custom_id: str = "citmod") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.cities = TextInput(label="Cities", placeholder="Enter a city here")
        self.add_item(self.cities)

    async def on_submit(self, interaction: Interaction) -> None:
        cities = parse_cities(self.cities.value)
        for city in cities:
            if not is_valid_city(city):
                await interaction.response.send_message(f"{city} doesn't appear to be a valid city.\n\n"
                                                        "Start a new conversation with the bot.",
                                                        ephemeral=True)
                return
        await interaction.response.send_message(f"Added {", ".join(cities)} cities to the list.",
                                                ephemeral=True)
        self.stop()


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
                                                                color=ERROR,
                                                                description="Please, specify a valid integer value in "
                                                                "range between 1 and 24."))
            return

        cfg: dict[str, Any] = get_server_config(cast(Guild, interaction.guild))
        fetcher: AODFetcher = AODFetcher(cfg["fetch_server"])
        data: Optional[List[dict[str, Any]]] = fetcher.fetch_gold(count + 1)
        if not data:
            await interaction.response.send_message(embed=Embed(title=":red_circle: There was an error",
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

        await interaction.response.send_message(embed=embed)

    @gold.error
    async def raise_gold_error(self, interaction: Interaction, error: Any) -> None:
        if isinstance(error, BadArgument):
            await interaction.response.send_message(embed=Embed(title=":red_circle: Invalid argument!",
                                                                color=ERROR,
                                                                description="Please, specify a valid integer value in range "
                                                                "between 1 and 24."))


    @command(name="price", description="Retrieves price of an item.")
    @describe(item_name="The Albion Online Data Project API item name.")
    @guild_only()
    async def price(self, interaction: Interaction, item_name: str) -> None:
        if not AODFetcher.exists(item_name):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name} doesn't exist!",
                                                          color=ERROR,
                                                          description=f"{item_name} is not an existing item!"))
            return

        view = PriceView(timeout=60)
        await interaction.response.send_message(embed=Embed(title="Price fetcher",
                                                            color=PRICE,
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
            quality_input: TextInput = cast(TextInput, view.quality_modal.children[0])
            cities_input: TextInput = cast(TextInput, view.cities_modal.children[0])
            quality: int = 1 if not quality_input.value else int(quality_input.value)
            cities: List[str] = [] if not cities_input.value else parse_cities(cities_input.value)

            cfg = get_server_config(cast(Guild, interaction.guild))
            fetcher: AODFetcher = AODFetcher(cfg["fetch_server"])
            renderer: SBIRenderFetcher = SBIRenderFetcher()
            data: Optional[List[dict[str, Any]]] = fetcher.fetch_price(item_name, quality, cities)
            if not data:
                await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                            color=ERROR,
                                                            description="I couldn't handle you request due to "
                                                            "a server problem. Try again later."),
                                                ephemeral=True)

                return

            embed: Embed = Embed(title=f"{data[0]["item_id"]} price",
                                 color=PRICE,
                                 description=f"Here are the prices of {data[0]["item_id"]} in different "
                                 "cities. You can find the full list of item [here](https://github.com/"
                                 "ao-data/ao-bin-dumps/blob/master/formatted/items.txt).")
            embed.set_thumbnail(url=renderer.fetch_item(item_name, quality))
            embed.set_footer(text="The data is provided by the Albion Online Data Project.")

            for entry in data:
                embed.add_field(name=f"{entry["city"]}",
                                value=f"Updated at: **{convert_api_timestamp(entry["sell_price_min_date"])}** "
                                f"and **{convert_api_timestamp(entry["buy_price_max_date"])}**\n"
                                f"Sold at: **{entry["sell_price_min"]}**\n"
                                f"Bought at: **{entry["buy_price_max"]}**")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=Embed(title=":red_circle: Timed out!",
                                                        color=ERROR,
                                                        description="Your time has run out. Start a new "
                                                        "conversation with the bot to get the price."),
                                            ephemeral=True)

    @price.error
    async def raise_price_error(self, interaction: Interaction, error: Any) -> None:
        if isinstance(error, BadArgument):
            await interaction.response.send_message(embed=Embed(title=":red_circle: Invalid argument!",
                                                                color=ERROR))
