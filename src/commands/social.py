#!/usr/bin/env python3
from typing import Any, Optional, cast
from discord import Color, Embed, Guild, Interaction
from discord.app_commands import command, describe, guild_only
from discord.ext.commands import Bot, Cog
from src.api import SandboxInteractiveInfo
from src.client import SERVERS
from src.components.cards import MembersCard, PlayerCard
from src.utils.formatting import inttoemoji_server
from src.utils.embeds import NameErrorEmbed, OutdatedDataErrorEmbed


class Social(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command(name="player", description="Displays detailed information about a player.")
    @describe(name="Name of the player you are looking for.")
    @guild_only()
    async def player(self, interaction: Interaction, name: str) -> None:
        fetcher: SandboxInteractiveInfo = SandboxInteractiveInfo(SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"])
        player: Optional[dict[str, Any]] = await fetcher.get_player(name)
        if not player:
            await interaction.response.send_message(embed=NameErrorEmbed(name), ephemeral=True)
            return

        embed: Embed = Embed(title=f"👨 {player["Name"]}",
                      color=Color.brand_green(),
                      description="Use `/deaths` to get more information about the"
                      " player's deaths or use `/kills` to get more information "
                      "about the player's kills.")
        if len(player["GuildName"]) != 0:
            embed.add_field(name="🛡️ Guild", value=f"{player["GuildName"]}")
        if len(player["AllianceName"]) != 0:
            embed.add_field(name="🤝 Alliance", value=f"{player["AllianceName"]}")
        embed.add_field(name="📚 Total fame", value=f"**{(player["KillFame"] + player["LifetimeStatistics"]["PvE"]["Total"] + player["LifetimeStatistics"]["Gathering"]["All"]["Total"] + player["LifetimeStatistics"]["Crafting"]["Total"] + player["LifetimeStatistics"]["FishingFame"] + player["LifetimeStatistics"]["FarmingFame"]):,}**", inline=False)
        embed.add_field(name="🛠️ Crafting fame", value=f"**{player["LifetimeStatistics"]["Crafting"]["Total"]:,}**", inline=False)

        embed.add_field(name="👾 PvE fame", value=f"**{player["LifetimeStatistics"]["PvE"]["Total"]:,}**")
        embed.add_field(name="🗡️ Kill fame", value=f"**{player["KillFame"]:,}**")
        embed.add_field(name="💀 Death fame", value=f"**{player["DeathFame"]:,}**")

        for typee, emoji in zip(("Fiber", "Hide", "Ore", "Rock", "Wood"), ('🌿', '🐘', '🍫', '🪨', '🌳')):
            embed.add_field(name=f"{emoji} {typee} fame", value=f"**{player["LifetimeStatistics"]["Gathering"][typee]["Total"]:,}**")
        embed.add_field(name="🐟 Fishing fame", value=f"**{player["LifetimeStatistics"]["FishingFame"]:,}**")

        embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=f"The data is provided by Sandbox Interactive GmbH. | {inttoemoji_server(SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"])} server")
        await interaction.response.send_message(embed=embed)


    @command(name="deaths", description="Displays recent deaths of a player.")
    @describe(name="Name of the player you are looking for.")
    @guild_only()
    async def deaths(self, interaction: Interaction, name: str) -> None:
        fetcher: SandboxInteractiveInfo = SandboxInteractiveInfo(SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"])
        deaths: Optional[list[dict[str, Any]]] = await fetcher.get_deaths(name)
        if deaths == None:
            await interaction.response.send_message(embed=NameErrorEmbed(name), ephemeral=True)
            return
        elif len(deaths) == 0:
            await interaction.response.send_message(embed=OutdatedDataErrorEmbed(), ephemeral=True)
            return

        card: PlayerCard = PlayerCard(interaction, deaths)
        await card.handle_message()
        card.message = await interaction.original_response()


    @command(name="kills", description="Displays recent kills of a player")
    @describe(name="Name of the player you are looking for.")
    @guild_only()
    async def kills(self, interaction: Interaction, name: str) -> None:
        fetcher: SandboxInteractiveInfo = SandboxInteractiveInfo(SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"])
        kills: Optional[list[dict[str, Any]]] = await fetcher.get_kills(name)
        if kills == None:
            await interaction.response.send_message(embed=NameErrorEmbed(name), ephemeral=True)
            return
        elif len(kills) == 0:
            await interaction.response.send_message(embed=OutdatedDataErrorEmbed(), ephemeral=True)
            return

        card: PlayerCard = PlayerCard(interaction, kills, is_kill=True)
        await card.handle_message()
        card.message = await interaction.original_response()


    @command(name="guild", description="Displays detailed information about a guild.")
    @describe(name="Name of the guild you are looking for.")
    @guild_only()
    async def guild(self, interaction: Interaction, name: str) -> None:
        fetcher: SandboxInteractiveInfo = SandboxInteractiveInfo(SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"])
        guild: Optional[dict[str, Any]] = await fetcher.get_guild(name)
        if not guild:
            await interaction.response.send_message(embed=NameErrorEmbed(name), ephemeral=True)
            return

        embed: Embed = Embed(title=f"🛡️ {guild["guild"]["Name"]}",
                             color=Color.brand_green(),
                             description="Use `/members` to get the list of guild members.")
        embed.add_field(name=":man: Founder", value=f"**{guild["guild"]["FounderName"]}**")
        if len(guild["guild"]["AllianceTag"]) != 0:
            embed.add_field(name="🤝 Alliance", value=f"**{guild["guild"]["AllianceTag"]}**")
        embed.add_field(name="👨 Members", value=f"**{guild["basic"]["memberCount"]}**")
        embed.add_field(name="📚 Fame", value=f"**{guild["overall"]["fame"]:,}**")
        embed.add_field(name="🗡️ Kills", value=f"**{guild["overall"]["kills"]:,}**")
        embed.add_field(name="🗡️📚 Kill fame", value=f"**{guild["guild"]["killFame"]:,}**")
        embed.add_field(name="💀 Deaths", value=f"**{guild["overall"]["deaths"]:,}**")
        embed.add_field(name="💀📚 Death fame", value=f"**{guild["guild"]["DeathFame"]:,}**")
        embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=f"The data is provided by Sandbox Interactive GmbH. | {inttoemoji_server(SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"])} server")
        await interaction.response.send_message(embed=embed)


    @command(name="members", description="Displays the list of players in the guild.")
    @describe(name="Name of the guild you are looking for")
    @guild_only()
    async def members(self, interaction: Interaction, name: str) -> None:
        fetcher: SandboxInteractiveInfo = SandboxInteractiveInfo(SERVERS.get_config(cast(Guild, interaction.guild))["fetch_server"])
        members: Optional[list[dict[str, Any]]] = await fetcher.get_members(name)
        if members == None:
            await interaction.response.send_message(embed=NameErrorEmbed(name), ephemeral=True)
            return
        elif len(members) == 0:
            await interaction.response.send_message(embed=OutdatedDataErrorEmbed(),ephemeral=True)
            return

        card: MembersCard = MembersCard(interaction, members)
        await card.handle_message()
        card.message = await interaction.original_response()


async def setup(bot: Bot) -> None:
    await bot.add_cog(Social(bot))
