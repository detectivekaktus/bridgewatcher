#!/usr/bin/env python3
from typing import Any, List, Optional, cast
from discord import Embed, Guild, Interaction
from discord.app_commands import command, describe, guild_only
from discord.ext.commands import Bot, Cog
from src import CITIES, CRAFTING_COLOR, DEFAULT_RATE, ERROR_COLOR, BONUS_RATE
from src.api import AODFetcher, ItemManager, SBIRenderFetcher
from src.components.ui import CraftingView
from src.config.config import get_server_config
from src.market import Crafter, find_crafting_bonus_city, find_least_expensive_city, find_most_expensive_city


class CalcsCog(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot: Bot = bot


    @command(name="craft", description="Calculates crafting profit from crafting an item")
    @describe(item_name="The Albion Online Data Project API item name.")
    @guild_only()
    async def craft(self, interaction: Interaction, item_name: str) -> None:
        item_name = item_name.upper()

        if (ItemManager.is_enchanted(item_name) and int(item_name[1]) < 4) or (not ItemManager.exists(item_name)):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name} doesn't exist!",
                                                                color=ERROR_COLOR,
                                                                description=f"{item_name} is not an existing item!"))
            return

        if not ItemManager.is_craftable(item_name):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name} is not craftable!",
                                                                color=ERROR_COLOR,
                                                                description="You can't craft uncraftable item!"))
            return

        view: CraftingView = CraftingView(item_name, timeout=120)
        view.is_enchanted = ItemManager.is_enchanted(item_name)
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
            message = await interaction.original_response()
            await message.delete()

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

            craft_city: str = view.craft_city[0] if view.craft_city else ""
            sell_city: str = view.sell_city[0] if view.sell_city else ""
            if not craft_city:
                if (city := find_crafting_bonus_city(item_name[:-2] if view.is_enchanted else item_name)) != None:
                    craft_city = city
                    if view.return_rate == DEFAULT_RATE:
                        view.return_rate = BONUS_RATE
                else:
                    craft_city = find_least_expensive_city(data)
            if not sell_city:
                sell_city = find_most_expensive_city(data, include_black_market=True if not ItemManager.is_resource(item_name) else False)

            resource_prices: dict[str, int] = {}
            for resource in view.crafting_requirements.keys():
                resource_data = fetcher.fetch_price(resource, qualities=1, cities=[craft_city.lower()])
                if not resource_data:
                    await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                                color=ERROR_COLOR,
                                                                description="I couldn't handle your request due to "
                                                                "a server problem. Try again later."),
                                                    ephemeral=True)
                    return
                resource_prices[resource] = resource_data[0]["sell_price_min"]

            crafter: Crafter = Crafter(resource_prices, view.resources, view.crafting_requirements, view.return_rate)
            result: dict[str, Any] = crafter.printable(data[CITIES.index(sell_city.lower())])
            embed: Embed = Embed(title=f"Crafting {item_name}...",
                                 color=CRAFTING_COLOR,
                                 description=f"This is a brief summary of crafting {item_name}"
                                 f" in **{craft_city.capitalize()}** with the sell destination"
                                 f" in **{sell_city.capitalize()}**.\n\n"

                                 f"You profit is expected to be **{result["profit"]:,} silver**, given by:\n"
                                 f"{result["sell_price"]:,} sell price\n"
                                 f"-{result["raw_cost"]:,} resource cost\n"
                                 f"+{result["unused_resources_price"]:,} unused resources")
            embed.add_field(name="Craft city", value=f"**{craft_city.capitalize()}**")
            embed.add_field(name="Sell city", value=f"**{sell_city.capitalize()}**")
            embed.set_thumbnail(url=SBIRenderFetcher.fetch_item(item_name, quality=1))
            embed.set_footer(text="The data is provided by the Albion Online Data Project.")
            for field in result["fields"]:
                embed.add_field(name=field["title"], value=f"**{field["value"]}**")

            await interaction.followup.send(embed=embed)
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=Embed(title=":red_circle: Timed out!",
                                                        color=ERROR_COLOR,
                                                        description="Your time has run out. Start a new "
                                                        "conversation with the bot to craft something."),
                                            ephemeral=True)
