#!/usr/bin/env python3
from typing import Any, Optional, cast
from discord import Color, Embed, Guild, Interaction
from discord.app_commands import command, describe, guild_only
from discord.ext.commands import Bot, Cog
from src import ITEM_NAMES
from src.constants import CITIES, DEFAULT_RATE, BONUS_RATE
from src.api import ItemManager, SandboxInteractiveRenderer
from src.client import DATABASE, MANAGER, SERVERS
from src.components.ui import CraftingView, FlipView
from src.market import NON_PREMIUM_TAX, PREMIUM_TAX, Crafter, find_crafting_bonus_city, find_least_expensive_city, find_most_expensive_city
from src.utils.formatting import format_name, get_city_data, strtoquality_int, inttoemoji_server
from src.utils.embeds import NameErrorEmbed, OutdatedDataErrorEmbed, ServerErrorEmbed, TimedOutErrorEmbed
from src.utils.logging import LOGGER


class Calcs(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command(name="craft", description="Calculates crafting profit from crafting an item")
    @describe(item_name="The Albion Online item name.")
    @guild_only()
    async def craft(self, interaction: Interaction, item_name: str, has_premium: bool) -> None:
        item_name = item_name.lower()

        if item_name not in ITEM_NAMES.keys():
            await interaction.response.send_message(embed=NameErrorEmbed(item_name), ephemeral=True)
            return

        if not ItemManager.is_craftable(DATABASE, ITEM_NAMES[item_name]):
            await interaction.response.send_message(embed=Embed(title=f"🔴 {format_name(item_name)} is not craftable!",
                                                                color=Color.red(),
                                                                description="You can't craft uncraftable item!"),
                                                    ephemeral=True)
            return

        view: CraftingView = CraftingView(ITEM_NAMES[item_name], ItemManager.is_enchanted(ITEM_NAMES[item_name]), timeout=120)
        await interaction.response.send_message(embed=Embed(title="🛠️ Crafting calculator",
                                                            color=Color.magenta(),
                                                            description="Let's craft something! Use the 🔘 buttons below"
                                                            " to access the full power of the crafting calculator! If"
                                                            " you are completely new to this bot, follow [this link]("
                                                            "https://github.com/detectivekaktus/bridgewatcher) to "
                                                            "explore more."),
                                                view=view,
                                                ephemeral=True)
        if not await view.wait():
            message = await interaction.original_response()
            await message.delete()

            server: int = SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"]
            data: Optional[list[dict[str, Any]]] = await MANAGER.get(ITEM_NAMES[item_name], server)
            if not data:
                await interaction.followup.send(embed=ServerErrorEmbed(), ephemeral=True)
                return

            craft_city: str = view.craft_city[0] if view.craft_city else ""
            sell_city: str = view.sell_city[0] if view.sell_city else ""
            if not craft_city:
                if (city := find_crafting_bonus_city(ITEM_NAMES[item_name])) != None:
                    craft_city = city
                    if view.return_rate == DEFAULT_RATE:
                        view.return_rate = BONUS_RATE
                else:
                    LOGGER.warning(f"Couldn't find crafting bonus city for {ITEM_NAMES[item_name]}.")
                    craft_city = find_least_expensive_city(data)
            if not sell_city:
                sell_city = find_most_expensive_city(data, include_black_market=True if not ItemManager.is_resource(DATABASE, ITEM_NAMES[item_name]) else False)

            resource_prices: dict[str, int] = {}
            for resource in view.crafting_requirements.keys():
                global_resource_data: list[dict[str, Any]] | None = await MANAGER.get(resource, server)
                if not global_resource_data:
                    await interaction.followup.send(embed=ServerErrorEmbed(), ephemeral=True)
                    return
                resource_data: dict[str, Any] = get_city_data(global_resource_data, craft_city)
                if resource_data["sell_price_min"] == 0:
                    await interaction.followup.send(embed=OutdatedDataErrorEmbed(), ephemeral=True)
                    return
                resource_prices[resource] = resource_data["sell_price_min"]

            crafter: Crafter = Crafter(resource_prices, view.resources if view.resources else view.crafting_requirements, view.crafting_requirements, view.return_rate, has_premium)
            result: dict[str, Any] = crafter.printable(data[CITIES.index(sell_city.lower())])
            embed: Embed = Embed(title=f"🛠️ Crafting {format_name(item_name)}",
                                 color=Color.magenta(),
                                 description=f"This is a brief summary of crafting {format_name(item_name)}"
                                 f" in **{craft_city.title()}** with the sell destination"
                                 f" in **{sell_city.title()}**.\n\n"

                                 f"Your profit is expected to be **{result["profit"]:,} silver**, given by:\n"
                                 f"+{result["sell_price"]:,} sell price\n"
                                 f"-{result["tax"]:,} taxes\n"
                                 f"-{result["raw_cost"]:,} resource cost\n"
                                 f"+{result["unused_resources_price"]:,} unused resources")
            embed.add_field(name="🏭 Craft city", value=f"**{craft_city.title()}**")
            embed.add_field(name="🏪 Sell city", value=f"**{sell_city.title()}**")
            embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_thumbnail(url=SandboxInteractiveRenderer.fetch_item(ITEM_NAMES[item_name], quality=1))
            embed.set_footer(text=f"The data is provided by the Albion Online Data Project | {inttoemoji_server(server)} server.")
            for field in result["fields"]:
                embed.add_field(name=field["title"], value=f"**{field["value"]}**")
            for unused_materials in result["unused_materials"]:
                embed.add_field(name=unused_materials["name"], value=f"**{unused_materials["value"]}**")
            await interaction.followup.send(embed=embed)
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=TimedOutErrorEmbed(), ephemeral=True)


    @command(name="flip", description="Calculates the profit of transportation of one item from city you select to the black market.")
    @describe(item_name="The Albion Online item name.")
    @guild_only()
    async def flip(self, interaction: Interaction, item_name: str, has_premium: bool) -> None:
        item_name = item_name.lower()

        if item_name not in ITEM_NAMES.keys():
            await interaction.response.send_message(embed=NameErrorEmbed(item_name), ephemeral=True)
            return

        if not ItemManager.is_sellable_on_black_market(DATABASE, ITEM_NAMES[item_name]):
            await interaction.response.send_message(embed=Embed(title=f"🔴 {format_name(item_name)} is not sellable on the black market!",
                                                                color=Color.red(),
                                                                description="You can't sell what is unsellable on the black market."),
                                                    ephemeral=True)
            return

        view: FlipView = FlipView(timeout=30)
        await interaction.response.send_message(embed=Embed(title=f"📦 Market flipper",
                                                            color=Color.orange(),
                                                            description="Let's flip the market up! Customize the item"
                                                            " you want to flip with 🔘 the interaction buttons below. If"
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
            server: int = SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"]
            data: Optional[list[dict[str, Any]]] = await MANAGER.get(ITEM_NAMES[item_name], server, quality)
            if not data:
                await interaction.followup.send(embed=ServerErrorEmbed(), ephemeral=True)
                return

            data = [get_city_data(data, view.cities[1]), get_city_data(data, view.cities[0])]
            
            if not data[0]["sell_price_min"] or not data[1]["sell_price_min"]:
                await interaction.followup.send(embed=OutdatedDataErrorEmbed(), ephemeral=True)
                return
            tax: int = int(data[0]["sell_price_min"] * (PREMIUM_TAX if has_premium else NON_PREMIUM_TAX) / 100)
                
            embed: Embed = Embed(title=f"📦 Flipping the market for {format_name(item_name)}",
                                 color=Color.orange(),
                                 description=f"The expected profit of transporting {format_name(item_name)} of **{view.quality.lower()}"
                                 f" quality** from **{view.cities[0].title()}** to the black market is:\n"
                                 f"* **{(data[0]["sell_price_min"] - tax - data[1]["sell_price_min"]):,} silver**\n"
                                 f"* **{round(((data[0]["sell_price_min"] - tax) / data[1]["sell_price_min"] * 100) - 100, 2):,}%**")
            embed.add_field(name="🌆 Start city", value=f"**{view.cities[0].title()}**")
            embed.add_field(name="💲 Buy price", value=f"**{data[1]["sell_price_min"]:,}**")
            embed.add_field(name="💸 Sell price", value=f"**{data[0]["sell_price_min"]:,}**")
            embed.add_field(name="💲 Tax", value=f"**{tax:,}**")
            embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_thumbnail(url=SandboxInteractiveRenderer.fetch_item(ITEM_NAMES[item_name], quality=quality))
            embed.set_footer(text=f"The data is provided by the Albion Online Data Project | {inttoemoji_server(server)} server.")
            await interaction.followup.send(embed=embed)
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=TimedOutErrorEmbed(), ephemeral=True)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Calcs(bot))
