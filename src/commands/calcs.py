#!/usr/bin/env python3
from typing import Any, List, Optional, cast
from json import loads
from sqlite3 import Connection, Cursor, connect
from random import choice
from discord import ButtonStyle, Embed, Guild, Interaction
from discord.app_commands import command, describe, guild_only
from discord.ext.commands import Bot, Cog
from discord.ui import Button, Modal, TextInput, View, button
from src import CITIES, CRAFTING_COLOR, ERROR_COLOR, BONUS_RATE
from src.api import AODFetcher, SBIRenderFetcher, is_valid_city, parse_cities
from src.config.config import get_server_config
from src.calc import Crafter, find_crafting_bonus_city, find_least_expensive_city, find_most_expensive_city


class CraftingView(View):
    def __init__(self, item_name: str, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.item_name: str = item_name
        self.craft_city: Optional[str] = None
        self.sell_city: Optional[str] = None
        self.resources: dict[str, int] = {}
        self.crafting_requirements: dict[str, int] = {}
        self.return_rate: float = 15


    @button(label="Craft city", style=ButtonStyle.gray)
    async def craft_city_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(CityModal(self, title="Craft city"))

    @button(label="Sell city", style=ButtonStyle.gray)
    async def sell_city_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(CityModal(self, title="Sell city", is_craft_city=False))

    @button(label="Resources", style=ButtonStyle.blurple)
    async def resources_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(ResourcesModal(self))

    @button(label="Return rate", style=ButtonStyle.blurple)
    async def return_rate_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(ReturnModal(self))

    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self.stop()


class CityModal(Modal):
    def __init__(self, view: CraftingView, *, is_craft_city: bool = True, title: str = "Title", timeout: Optional[float] = None, custom_id: str = "city") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.view: CraftingView = view
        self.is_craft_city: bool = is_craft_city
        self.city: TextInput = TextInput(label=title, placeholder="Enter one city here")
        self.add_item(self.city)


    async def on_submit(self, interaction: Interaction) -> None:
        cities: List[str] = parse_cities(self.city.value.strip())
        if len(cities) > 1:
            await interaction.response.send_message("You can't enter more than 1 city.",
                                                    ephemeral=True,
                                                    delete_after=5)
            return

        if not is_valid_city(cities[0]):
            await interaction.response.send_message("The city you entered is not valid.",
                                                    ephemeral=True,
                                                    delete_after=5)
            return
        
        if self.is_craft_city:
            self.view.craft_city = cities[0]
        else:
            self.view.sell_city = cities[0]
        await interaction.response.defer()


class ResourcesModal(Modal):
    def __init__(self, view: CraftingView, *, title: str = "Resources", timeout: Optional[float] = None, custom_id: str = "resources") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.view = view

        conn: Connection = connect("res/items.db")
        curs: Cursor = conn.cursor()
        curs.execute("SELECT * FROM items WHERE name = ?", (self.view.item_name, ))
        res: List[dict[str, Any]] | dict[str, Any] = loads(curs.fetchone()[4])
        requirements: List[dict[str, Any]] = res["craftresource"] if isinstance(res, dict) else res[0]["craftresource"]
        conn.commit()
        conn.close()
        
        self.txt_inputs: List[TextInput] = []
        placeholders = ("Eg. 100", "Eg. 3350", "Eg. 305", "Eg. 777")
        
        for requirement in requirements:
            self.view.crafting_requirements[requirement["@uniquename"]] = int(requirement["@count"])
            txt_input = TextInput(label=requirement["@uniquename"], placeholder=choice(placeholders))
            self.txt_inputs.append(txt_input)
            self.add_item(txt_input)

    async def on_submit(self, interaction: Interaction) -> None:
        for txt_input in self.txt_inputs:
            try:
                value = int(txt_input.value)
                self.view.resources[txt_input.label] = value
            except ValueError:
                await interaction.response.send_message("Some of your resource values are not valid.",
                                                        ephemeral=True,
                                                        delete_after=5)

        await interaction.response.defer()


class ReturnModal(Modal):
    def __init__(self, view: CraftingView, *, title: str = "Return rate", timeout: Optional[float] = None, custom_id: str = "rrate") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.view = view
        self.return_rate: TextInput = TextInput(label=title, placeholder="Eg. 15 or 25.5")
        self.add_item(self.return_rate)


    async def on_submit(self, interaction: Interaction) -> None:
        try:
            return_rate: float = float(self.return_rate.value)
            if return_rate >= 100 or return_rate < 0:
                raise ValueError("Return rate can't be more than 99 percent and can't be below 0 percent.")
            self.view.return_rate = return_rate
            await interaction.response.defer()
        except ValueError:
            await interaction.response.send_message(f"{self.return_rate.value} is not a valid return rate.")


class CalcsCog(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot: Bot = bot


    @command(name="craft", description="Calculates crafting profit from crafting an item")
    @describe(item_name="The Albion Online Data Project API item name.")
    @guild_only()
    async def craft(self, interaction: Interaction, item_name: str) -> None:
        item_name = item_name.upper()

        if AODFetcher.is_enchanted(item_name):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: I am a potato!",
                                                                color=ERROR_COLOR,
                                                                description="My master haven't taught me how to craft"
                                                                " enchanted items! Wait for an update to start crafting"
                                                                " enchanted items with me."))
            return

        if not AODFetcher.exists(item_name):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name} doesn't exist!",
                                                                color=ERROR_COLOR,
                                                                description=f"{item_name} is not an existing item!"))
            return

        if not AODFetcher.is_craftable(item_name):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name} is not craftable!",
                                                                color=ERROR_COLOR,
                                                                description="You can't craft uncraftable item!"))
            return

        view: CraftingView = CraftingView(item_name, timeout=120)
        await interaction.response.send_message(embed=Embed(title="Crafting calculator",
                                                            color=CRAFTING_COLOR,
                                                            description="Let's craft something! Use the buttons below"
                                                            " to access the full power of the crafting calculator!\n\n"
                                                            
                                                            "Use `Craft city` button to set the city where you"
                                                            " want to craft the item. Default is the city with "
                                                            "crafting bonus.\n\n"

                                                            "Use `Sell city` button to set the city where you "
                                                            "want to sell the item. Default is the most expensive"
                                                            " city.\n\n"

                                                            "Use `Resouces` button to set the amount of resouces"
                                                            " you have to produce the item you selected.\n\n"

                                                            "Use `Return rate` button to set the return rate of"
                                                            " the resources you're using to craft the item selected."),
                                                view=view,
                                                ephemeral=True)
        if not await view.wait():
            if len(view.resources) == 0:
                await interaction.followup.send(embed=Embed(title=":red_circle: No resources specified!",
                                                            color=ERROR_COLOR,
                                                            description="You need to specify the resources you have"
                                                            " to craft the item. Start a new conversation with the "
                                                            "bot to craft something."),
                                                ephemeral=True)
                return

            fetcher: AODFetcher = AODFetcher(get_server_config(cast(Guild, interaction.guild))["fetch_server"])
            data: Optional[List[dict[str, Any]]] = fetcher.fetch_price(item_name, qualities=1)
            if not data:
                await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                            color=ERROR_COLOR,
                                                            description="I couldn't handle your request due to "
                                                            "a server problem. Try again later."),
                                                ephemeral=True)

                return
            if not view.craft_city:
                if (city := find_crafting_bonus_city(item_name)) != None:
                    view.craft_city = city
                    if view.return_rate == 15:
                        view.return_rate = BONUS_RATE
                else:
                    view.craft_city = find_least_expensive_city(data)
            if not view.sell_city:
                view.sell_city = find_most_expensive_city(data)

            resource_prices: dict[str, int] = {}
            for resource in view.crafting_requirements.keys():
                resource_data = fetcher.fetch_price(resource, qualities=1, cities=[view.craft_city.lower()])
                if not resource_data:
                    await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                                color=ERROR_COLOR,
                                                                description="I couldn't handle your request due to "
                                                                "a server problem. Try again later."),
                                                    ephemeral=True)
                    return

                resource_prices[resource] = resource_data[0]["sell_price_min"]

            print(data[CITIES.index(view.sell_city.lower())])
            [print(title, price) for title, price in resource_prices.items()]

            crafter: Crafter = Crafter(item_name, resource_prices, view.resources, view.crafting_requirements, view.return_rate)
            result: dict[str, Any] = crafter.printable(data[CITIES.index(view.sell_city.lower())])
            embed: Embed = Embed(title=f"Crafting {item_name}...",
                                 color=CRAFTING_COLOR,
                                 description=f"This is a brief summary of crafting {item_name}"
                                 f" in **{view.craft_city.capitalize()}** with the sell destination"
                                 f" in **{view.sell_city.capitalize()}**.\n\n"

                                 f"You profit is expected to be **{result["profit"]:,} silver**, given by:\n"
                                 f"{result["sell_price"]:,} sell price\n"
                                 f"-{result["raw_cost"]:,} resource cost\n"
                                 f"+{result["unused_resources_price"]:,} unused resources")
            embed.add_field(name="Craft city", value=f"**{view.craft_city.capitalize()}**")
            embed.add_field(name="Sell city", value=f"**{view.sell_city.capitalize()}**")
            embed.set_thumbnail(url=SBIRenderFetcher.fetch_item(item_name, quality=1))
            embed.set_footer(text="The data is provided by the Albion Online Data Project.")
            for field in result["fields"]:
                embed.add_field(name=field["title"], value=f"**{field["value"]}**")

            await interaction.followup.send(embed=embed)
            message = await interaction.original_response()
            await message.delete()
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=Embed(title=":red_circle: Timed out!",
                                                        color=ERROR_COLOR,
                                                        description="Your time has run out. Start a new "
                                                        "conversation with the bot to craft something."),
                                            ephemeral=True)
