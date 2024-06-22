#!/usr/bin/env python3
from typing import Any, List, Optional, cast
from discord import Color, Embed, Guild, Interaction
from discord.app_commands import command, describe, guild_only
from discord.ext.commands import Bot, Cog
from src import CITIES, DEFAULT_RATE, BONUS_RATE, ITEM_NAMES
from src.api import AlbionOnlineData, ItemManager, SandboxInteractiveRenderer
from src.client import SERVERS
from src.components.ui import CraftingView, FlipView
from src.market import Crafter, find_crafting_bonus_city, find_least_expensive_city, find_most_expensive_city
from src.utils import strtoquality_int, inttoemoji_server


class Calcs(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command(name="craft", description="Calculates crafting profit from crafting an item")
    @describe(item_name="The Albion Online Data Project API item name.")
    @guild_only()
    async def craft(self, interaction: Interaction, item_name: str) -> None:
        item_name = item_name.lower()

        if item_name not in ITEM_NAMES.keys():
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name.title()} doesn't exist!",
                                                                color=Color.red(),
                                                                description=f"{item_name.title()} is not an existing item!"))
            return

        if not ItemManager.is_craftable(ITEM_NAMES[item_name]):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name.title()} is not craftable!",
                                                                color=Color.red(),
                                                                description="You can't craft uncraftable item!"))
            return

        view: CraftingView = CraftingView(ITEM_NAMES[item_name], timeout=120)
        view.is_enchanted = ItemManager.is_enchanted(ITEM_NAMES[item_name])
        await interaction.response.send_message(embed=Embed(title=":hammer_pick: Crafting calculator",
                                                            color=Color.magenta(),
                                                            description="Let's craft something! Use the buttons below"
                                                            " to access the full power of the crafting calculator! If"
                                                            " you are completely new to this bot, follow [this link]("
                                                            "https://github.com/detectivekaktus/bridgewatcher) to "
                                                            "explore more."),
                                                view=view,
                                                ephemeral=True)
        if not await view.wait():
            message = await interaction.original_response()
            await message.delete()

            if len(view.resources) == 0:
                await interaction.followup.send(embed=Embed(title=":red_circle: No resources specified!",
                                                            color=Color.red(),
                                                            description="You need to specify the resources you have"
                                                            " to craft the item. Start a new conversation with the "
                                                            "bot to craft something."),
                                                ephemeral=True)
                return

            server: int = SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"]
            fetcher: AlbionOnlineData = AlbionOnlineData(server)
            data: Optional[List[dict[str, Any]]] = fetcher.fetch_price(ITEM_NAMES[item_name], qualities=1)
            if not data:
                await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                            color=Color.red(),
                                                            description="I couldn't handle your request due to "
                                                            "a server problem. Try again later."),
                                                ephemeral=True)
                return

            craft_city: str = view.craft_city[0] if view.craft_city else ""
            sell_city: str = view.sell_city[0] if view.sell_city else ""
            if not craft_city:
                if (city := find_crafting_bonus_city(ITEM_NAMES[item_name])) != None:
                    craft_city = city
                    if view.return_rate == DEFAULT_RATE:
                        view.return_rate = BONUS_RATE
                else:
                    craft_city = find_least_expensive_city(data)
            if not sell_city:
                sell_city = find_most_expensive_city(data, include_black_market=True if not ItemManager.is_resource(ITEM_NAMES[item_name]) else False)

            resource_prices: dict[str, int] = {}
            for resource in view.crafting_requirements.keys():
                resource_data = fetcher.fetch_price(resource, qualities=1, cities=[craft_city.lower()])
                if not resource_data:
                    await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                                color=Color.red(),
                                                                description="I couldn't handle your request due to "
                                                                "a server problem. Try again later."),
                                                    ephemeral=True)
                    return
                resource_prices[resource] = resource_data[0]["sell_price_min"]

            crafter: Crafter = Crafter(resource_prices, view.resources, view.crafting_requirements, view.return_rate)
            result: dict[str, Any] = crafter.printable(data[CITIES.index(sell_city.lower())])
            embed: Embed = Embed(title=f":hammer_pick: Crafting {item_name.title()}",
                                 color=Color.magenta(),
                                 description=f"This is a brief summary of crafting {item_name.title()}"
                                 f" in **{craft_city.title()}** with the sell destination"
                                 f" in **{sell_city.title()}**.\n\n"

                                 f"You profit is expected to be **{result["profit"]:,} silver**, given by:\n"
                                 f"{result["sell_price"]:,} sell price\n"
                                 f"-{result["raw_cost"]:,} resource cost\n"
                                 f"+{result["unused_resources_price"]:,} unused resources")
            embed.add_field(name="Craft city", value=f"**{craft_city.title()}**")
            embed.add_field(name="Sell city", value=f"**{sell_city.title()}**")
            embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_thumbnail(url=SandboxInteractiveRenderer.fetch_item(ITEM_NAMES[item_name], quality=1))
            embed.set_footer(text=f"The data is provided by the Albion Online Data Project | {inttoemoji_server(server)} server.")
            for field in result["fields"]:
                embed.add_field(name=field["title"], value=f"**{field["value"]}**")
            await interaction.followup.send(embed=embed)
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=Embed(title=":red_circle: Timed out!",
                                                        color=Color.red(),
                                                        description="Your time has run out. Start a new "
                                                        "conversation with the bot to craft something."),
                                            ephemeral=True)


    @command(name="flip", description="Calculates profit of transportation of one item from city you select to the black market.")
    @describe(item_name="The Albion Online Data Project API item name.")
    @guild_only()
    async def flip(self, interaction: Interaction, item_name: str) -> None:
        item_name = item_name.lower()

        if item_name not in ITEM_NAMES.keys():
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name.title()} doesn't exist!",
                                                                color=Color.red(),
                                                                description=f"{item_name.title()} is not an existing item!"))
            return

        if not ItemManager.is_sellable_on_black_market(ITEM_NAMES[item_name]):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name.title()} is not sellable on the black market!",
                                                                color=Color.red(),
                                                                description="You can't sell what is unsellable on the black market."))
            return

        view: FlipView = FlipView(timeout=30)
        await interaction.response.send_message(embed=Embed(title=f":truck: Market flipper",
                                                            color=Color.random(),
                                                            description="Let's flip the market up! Customize the item"
                                                            " you want to flip with the interaction buttons below. If"
                                                            " you are completely new to this bot, follow the rules in"
                                                            "dicated [right here](https://github.com/detectivekaktus/"
                                                            "bridgewatcher)."),
                                                view=view,
                                                ephemeral=True)

        if not await view.wait():
            message = await interaction.original_response()
            await message.delete()

            quality: int = strtoquality_int(view.quality)
            view.cities.extend(["black market"] if view.cities else [cast(str, find_crafting_bonus_city(ITEM_NAMES[item_name])), "black market"])
            cities: List[str] = view.cities

            server: int = SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"]
            fetcher: AlbionOnlineData = AlbionOnlineData(server)
            data: Optional[List[dict[str, Any]]] = fetcher.fetch_price(ITEM_NAMES[item_name], quality, cities)
            if not data:
                await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                            color=Color.red(),
                                                            description="I couldn't handle your request due to "
                                                            "a server problem. Try again later."),
                                                ephemeral=True)
                return
            
            try:
                embed: Embed = Embed(title=f":truck: Flipping the market for {item_name.title()}",
                                     color=Color.random(),
                                     description=f"The expected profit of transporting {item_name.title()} of **{view.quality.lower()}"
                                     f" quality** from **{view.cities[0].title()}** to the black market is:\n"
                                     f"* **{(data[0]["sell_price_min"] - data[1]["sell_price_min"]):,} silver**\n"
                                     f"* **{round((data[0]["sell_price_min"] / data[1]["sell_price_min"] * 100) - 100, 2):,}%**")
                embed.add_field(name="Start city", value=f"**{view.cities[0].title()}**")
                embed.add_field(name="Buy price", value=f"**{data[1]["sell_price_min"]:,}**")
                embed.add_field(name="Sell price", value=f"**{data[0]["sell_price_min"]:,}**")
                embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_thumbnail(url=SandboxInteractiveRenderer.fetch_item(ITEM_NAMES[item_name], quality=quality))
                embed.set_footer(text=f"The data is provided by the Albion Online Data Project | {inttoemoji_server(server)} server.")
                await interaction.followup.send(embed=embed)
            except ZeroDivisionError:
                await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                            color=Color.red(),
                                                            description="I couldn't handle your request due to "
                                                            "a server problem. Try again later."),
                                                ephemeral=True)
                return
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=Embed(title=":red_circle: Timed out!",
                                                        color=Color.red(),
                                                        description="Your time has run out. Start a new "
                                                        "conversation with the bot to craft something."),
                                            ephemeral=True)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Calcs(bot))
