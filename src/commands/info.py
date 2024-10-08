#!/usr/bin/env python3
from datetime import datetime, timezone
from typing import Any, Optional, cast
from discord import Color, Embed, Guild, Interaction
from discord.app_commands import command, describe
from discord.ext.commands import Bot, Cog, guild_only
from src import ITEM_NAMES
from src.api import AlbionOnlineData, SandboxInteractiveRenderer, convert_api_timestamp, get_percent_variation
from src.client import MANAGER, SERVERS
from src.components.ui import PriceView
from src.utils import format_name, strtoquality_int, inttoemoji_server
from src.utils.embeds import InvalidValueErrorEmbed, NameErrorEmbed, ServerErrorEmbed, TimedOutErrorEmbed


class Info(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command(name="gold", description="Retieves gold prices.")
    @describe(count="Number of past gold prices.")
    @guild_only()
    async def gold(self, interaction: Interaction, count: int = 3) -> None:
        if count not in range(1, 25):
            await interaction.response.send_message(embed=InvalidValueErrorEmbed(count))
            return

        server: int = SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"]
        fetcher: AlbionOnlineData = AlbionOnlineData(server)
        data: Optional[list[dict[str, Any]]] = await fetcher.fetch_gold(count + 1)
        if not data:
            await interaction.response.send_message(embed=ServerErrorEmbed(), ephemeral=True)
            return

        embed: Embed = Embed(title="🪙 Gold prices",
                             color=Color.gold(),
                             description=f"Here are the past {count} gold prices.\n"
                             "Total percent variation in the specified period: "
                             f"**{round((data[0]["price"] / data[-1]["price"] - 1) * 100, 2):,}%**\n"
                             "Total numeric variation in the specified period: "
                             f"**{(data[0]["price"] - data[-1]["price"]):,}**")
        embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=f"The data is provided by the Albion Online Data Project | {inttoemoji_server(server)} server")

        for i in range(len(data) - 1):
            embed.add_field(name=f"⌛ Data from {convert_api_timestamp(data[i]["timestamp"])}.",
                            value=f"Gold price: **{data[i]["price"]}**\n"
                            f"Percent variation from the last value: **{get_percent_variation(data, i)}%**\n"
                            f"Numeric variation from the last value: **{data[i]["price"] - data[i + 1]["price"]}**")

        await interaction.response.send_message(embed=embed)


    @command(name="premium", description="Retrieves price of premium status in the game.")
    @guild_only()
    async def premium(self, interaction: Interaction) -> None:
        server: int = SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"]
        fetcher: AlbionOnlineData = AlbionOnlineData(server)
        data: Optional[list[dict[str, Any]]] = await fetcher.fetch_gold(1)
        
        if not data:
            await interaction.response.send_message(embed=ServerErrorEmbed(), ephemeral=True)
            return

        embed: Embed = Embed(title="👑 Premium status price",
                             color=Color.gold())
        embed.add_field(name="30 days", value=f"**{(data[0]["price"] * 3750):,}**")
        embed.add_field(name="90 days", value=f"**{(data[0]["price"] * 10500):,}**")
        embed.add_field(name="180 days", value=f"**{(data[0]["price"] * 19500):,}**")
        embed.add_field(name="360 days", value=f"**{(data[0]["price"] * 36000):,}**")
        embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=f"The data is provided by the Albion Online Data Project | {inttoemoji_server(server)} server")
        await interaction.response.send_message(embed=embed)


    @command(name="price", description="Retrieves price of an item.")
    @describe(item_name="The Albion Online item name.")
    @guild_only()
    async def price(self, interaction: Interaction, item_name: str) -> None:
        item_name = item_name.lower()

        if item_name not in ITEM_NAMES.keys():
            await interaction.response.send_message(embed=NameErrorEmbed(item_name), ephemeral=True)
            return

        view = PriceView(timeout=60)
        await interaction.response.send_message(embed=Embed(title="💲 Price fetcher",
                                                            color=Color.blurple(),
                                                            description="Let's search for a price together!"
                                                            " Use 🔘 the navigation buttons on the bottom of t"
                                                            "his message to customize your experience. If y"
                                                            "ou are new to this bot, follow [this link](htt"
                                                            "ps://github.com/detectivekaktus/bridgewatcher?"
                                                            "tab=readme-ov-file#how-do-i-use-this)"),
                                                view=view,
                                                ephemeral=True)
        if not await view.wait():
            message = await interaction.original_response()
            await message.delete()

            quality: int = strtoquality_int(view.quality)
            server: int = SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"]
            data: Optional[list[dict[str, Any]]] = await MANAGER.get(ITEM_NAMES[item_name], server, strtoquality_int(view.quality))
            if not data:
                await interaction.followup.send(embed=ServerErrorEmbed(), ephemeral=True)
                return

            embed: Embed = Embed(title=f"🔘 {format_name(item_name)} price", color=Color.blurple())
            embed.set_thumbnail(url=SandboxInteractiveRenderer.fetch_item(ITEM_NAMES[item_name], quality))
            embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=f"The data is provided by the Albion Online Data Project. | {inttoemoji_server(server)} server")

            description: list[str] = ["***Sell orders:***\n"]
            for entry in data:
                description.append(f"**{entry["city"]}** (updated {convert_api_timestamp(entry["sell_price_min_date"])}): **{entry["sell_price_min"]:,}**\n")

            description.append("\n***Buy orders:***\n")
            for entry in data:
                description.append(f"**{entry["city"]}** (updated {convert_api_timestamp(entry["sell_price_min_date"])}): **{entry["buy_price_max"]:,}**\n")
            
            embed.description = "".join(description)
            await interaction.followup.send(embed=embed)
        else:
            message = await interaction.original_response()
            await message.delete()
            await interaction.followup.send(embed=TimedOutErrorEmbed(), ephemeral=True)


    @command(name="utc", description="Displays current UTC time.")
    async def utc(self, interaction: Interaction) -> None:
        await interaction.response.send_message(f"Current UTC time: {datetime.now(timezone.utc).strftime("%b %d, %Y. %H:%M:%S")}")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Info(bot))
