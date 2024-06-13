#!/usr/bin/env python3
from typing import Any, List, Optional, cast
from discord import Color, Embed, Guild, Interaction
from discord.app_commands import command, describe
from discord.ext.commands import Bot, Cog, guild_only
from src.api import AlbionOnlineData, ItemManager, SandboxInteractiveRenderer, convert_api_timestamp, get_percent_variation, strquality_toint
from src.client import servers
from src.components.ui import PriceView


class Info(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command(name="gold", description="Retieves gold prices.")
    @describe(count="Number of past gold prices.")
    @guild_only()
    async def gold(self, interaction: Interaction, count: int = 3) -> None:
        if count not in range(1, 25):
            await interaction.response.send_message(embed=Embed(title=":red_circle: Invalid argument!",
                                                                color=Color.red(),
                                                                description="Please, specify a valid integer value in "
                                                                "range between 1 and 24."))
            return

        fetcher: AlbionOnlineData = AlbionOnlineData(servers.get_config(cast(Guild, interaction.guild))["fetch_server"])
        data: Optional[List[dict[str, Any]]] = fetcher.fetch_gold(count + 1)
        if not data:
            await interaction.response.send_message(embed=Embed(title=":red_circle: There was an error",
                                                                color=Color.red(),
                                                                description="I've encountered an error trying to get item "
                                                                "prices from the API. Please, try again later."))
            return

        embed: Embed = Embed(title=":coin: Gold prices",
                             color=Color.gold(),
                             description=f"Here are the past {count} gold prices.\n"
                             "Total percent variation in the specified period: "
                             f"**{round((data[0]["price"] / data[-1]["price"] - 1) * 100, 2):,}%**\n"
                             "Total numeric variation in the specified period: "
                             f"**{(data[0]["price"] - data[-1]["price"]):,}**")
        embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text="The data is provided by the Albion Online Data Project\n")

        for i in range(len(data) - 1):
            embed.add_field(name=f"Data from {convert_api_timestamp(data[i]["timestamp"])}.",
                            value=f"Gold price: **{data[i]["price"]}**\n"
                            f"Percent variation from the last value: **{get_percent_variation(data, i)}%**\n"
                            f"Numeric variation from the last value: **{data[i]["price"] - data[i + 1]["price"]}**")

        await interaction.response.send_message(embed=embed)


    @command(name="premium", description="Retrieves price of premium status in the game.")
    @guild_only()
    async def premium(self, interaction: Interaction) -> None:
        fetcher: AlbionOnlineData = AlbionOnlineData(servers.get_config(cast(Guild, interaction.guild))["fetch_server"])
        data: Optional[List[dict[str, Any]]] = fetcher.fetch_gold(1)
        
        if not data:
            await interaction.response.send_message(embed=Embed(title=":red_circle: There was an error",
                                                                color=Color.red(),
                                                                description="I've encountered an error trying to get item "
                                                                "prices from the API. Please, try again later."))
            return

        embed: Embed = Embed(title=":crown: Premium status price",
                             color=Color.gold())
        embed.add_field(name="30 days", value=f"**{(data[0]["price"] * 3750):,}**")
        embed.add_field(name="90 days", value=f"**{(data[0]["price"] * 10500):,}**")
        embed.add_field(name="180 days", value=f"**{(data[0]["price"] * 19500):,}**")
        embed.add_field(name="360 days", value=f"**{(data[0]["price"] * 36000):,}**")
        embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text="The data is provided by the Albion Online Data Project\n")
        await interaction.response.send_message(embed=embed)


    @command(name="price", description="Retrieves price of an item.")
    @describe(item_name="The Albion Online Data Project API item name.")
    @guild_only()
    async def price(self, interaction: Interaction, item_name: str) -> None:
        item_name = item_name.upper()

        if not ItemManager.exists(item_name):
            await interaction.response.send_message(embed=Embed(title=f":red_circle: {item_name} doesn't exist!",
                                                          color=Color.red(),
                                                          description=f"{item_name} is not an existing item!"))
            return

        view = PriceView(timeout=60)
        await interaction.response.send_message(embed=Embed(title=":dollar: Price fetcher",
                                                            color=Color.blurple(),
                                                            description="Let's search for a price together!"
                                                            " Use the navigation buttons on the bottom of t"
                                                            "his message to customize your experience. If y"
                                                            "ou are new to this bot, follow [this link](htt"
                                                            "ps://github.com/detectivekaktus/bridgewatcher?"
                                                            "tab=readme-ov-file#how-do-i-use-this)"),
                                                view=view,
                                                ephemeral=True)
        if not await view.wait():
            message = await interaction.original_response()
            await message.delete()

            quality: int = strquality_toint(view.quality)

            fetcher: AlbionOnlineData = AlbionOnlineData(servers.get_config(cast(Guild, interaction.guild))["fetch_server"])
            data: Optional[List[dict[str, Any]]] = fetcher.fetch_price(item_name, quality, cast(List[str], view.cities))
            if not data:
                await interaction.followup.send(embed=Embed(title=":red_circle: Error!",
                                                            color=Color.red(),
                                                            description="I couldn't handle you request due to "
                                                            "a server problem. Try again later."),
                                                ephemeral=True)

                return

            embed: Embed = Embed(title=f":dollar: {data[0]["item_id"]} price",
                                 color=Color.blurple())
            embed.set_thumbnail(url=SandboxInteractiveRenderer.fetch_item(item_name, quality))
            embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text="The data is provided by the Albion Online Data Project.")

            description: str = "***Sell orders:***\n"
            for entry in data:
                description += f"**{entry["city"]}** (updated at {convert_api_timestamp(entry["sell_price_min_date"])}): **{entry["sell_price_min"]:,}**\n"

            description += "\n***Buy orders:***\n"
            for entry in data:
                description += f"**{entry["city"]}** (updated at {convert_api_timestamp(entry["sell_price_min_date"])}): **{entry["buy_price_max"]:,}**\n"
            
            embed.description = description
            await interaction.followup.send(embed=embed)
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=Embed(title=":red_circle: Timed out!",
                                                        color=Color.red(),
                                                        description="Your time has run out. Start a new "
                                                        "conversation with the bot to get the price."),
                                            ephemeral=True)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Info(bot))
