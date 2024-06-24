#!/usr/bin/env python3
from typing import cast
from discord import Color, Embed, Guild, Interaction
from discord.app_commands import Choice, choices, describe, command
from discord.ext.commands import Bot, Cog, guild_only
from src.client import SERVERS
from src.utils import inttostr_server, strtoint_server, inttoemoji_server


class Settings(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command(name="server", description="Sets server to be operated by the bot.")
    @describe(server="Albion Online server to be used by the bot.")
    @choices(server=[Choice(name=name.capitalize(), value=name) for name in ("america", "europe", "asia")])
    @guild_only()
    async def server(self, interaction: Interaction, server: Choice[str]) -> None:
        fetch_server: int = strtoint_server(server.value)
        SERVERS.update_config(cast(Guild, interaction.guild), fetch_server)
        match fetch_server:
            case 1:
                await interaction.response.send_message("Server successfully changed to 🇺🇸 America.")
            case 2:
                await interaction.response.send_message("Server successfully changed to 🇪🇺 Europe.")
            case 3:
                await interaction.response.send_message("Server successfully changed to 🇨🇳 Asia.")
    

    @command(name="info", description="Provides basic information about the server.")
    @guild_only()
    async def info(self, interaction: Interaction) -> None:
        guild: Guild = cast(Guild, interaction.guild)
        embed: Embed = Embed(title=f"📖 Information about {guild.name}",
                             color=Color.orange(),
                             description=f"There you have a configuration info about {guild.name}.")
        server = SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"]
        embed.add_field(name="🌐 Albion Online server", value=f"{inttoemoji_server(server)} {inttostr_server(server).capitalize()}")
        embed.add_field(name="👨 Members of the server", value=guild.member_count)
        embed.add_field(name="👑 Server owner", value=f"<@{guild.owner_id}>")
        await interaction.response.send_message(embed=embed)


    @command(name="help", description="Provides basic information over the bot.")
    async def help(self, interaction: Interaction) -> None:
        embed = Embed(title=":wave: Hello!",
                      color=Color.teal(),
                      description="I'm Bridgewatcher, a Discord bot created by <@692305905123065918>.\n"
                      "I can help you with 🛠️ crafting, 🧱 refining, 🤝 trading, and"
                      " 📦 transporting goods 🌐 all around Albion on all the servers.\n\n"

                      "**My commands**\n"
                      "🤖 `/info`: get the configuration information\n"
                      "🌐 `/server`: set the Albion Online server\n"
                      "🪙 `/gold`: get price of gold\n"
                      "👑 `/premium`: get price of all types of premium status\n"
                      "🏷️ `/price`: search for any item price\n"
                      "🛠️ `/craft`: craft an item and get respective profit\n"
                      "💹 `/flip`: get profit of transporting an item from city to black market\n"
                      "⏰ `/utc`: get UTC time.\n"
                      "👨 `/player`: get general information about a player\n"
                      "💀 `/deaths`: get general information about the player's deaths\n"
                      "🗡️ `/kills`: get general information about the player's kills\n"
                      "🛡️ `/guild`: get general information about a guild\n"
                      "👨 `/members`: get members of the guild\n\n"
    
                      "**Found a bug?**\n"
                      "If the bot is behaving in unexpected way 🐞, please [report it to the developer]"
                      "(https://github.com/detectivekaktus/bridgewatcher/issues/new).")
        embed.set_author(name="Made by DetectiveKaktus", url="https://github.com/detectivekaktus")
        await interaction.response.send_message(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Settings(bot))
