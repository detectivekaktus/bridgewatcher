#!/usr/bin/env python3
from typing import Any, Optional, cast
from discord import Color, Embed, Guild, Interaction
from discord.app_commands import command, describe, guild_only
from discord.ext.commands import Bot, Cog
from src.api import SandboxInteractiveInfo
from src.client import servers


class Social(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command(name="player", description="Displays detailed information about a player.")
    @describe(name="The name of the player you are looking for.")
    @guild_only()
    async def player(self, interaction: Interaction, name: str) -> None:
        fetcher: SandboxInteractiveInfo = SandboxInteractiveInfo(servers.get_config(cast(Guild, interaction.guild))["fetch_server"])
        player: Optional[dict[str, Any]] = fetcher.get_player(name)
        if not player:
            await interaction.response.send_message(embed=Embed(title=f"{name} doesn't exist",
                                                                color=Color.red(),
                                                                description=f"No player with name {name} has been "
                                                                "found. Check if you changed the Albion Online  "
                                                                "server or try again later."))
            return

        embed: Embed = Embed(title=f":man: {player["Name"]}",
                      color=Color.brand_green(),
                      description="Use `/deaths` to get more information about the"
                      " player's deaths or use `/kills` to get more information "
                      "about the player's kills.")
        if len(player["GuildName"]) != 0:
            embed.add_field(name=":shield: Guild", value=f"{player["GuildName"]}")
        if len(player["AllianceName"]) != 0:
            embed.add_field(name=":handshake: Alliance", value=f"{player["AllianceName"]}")
        embed.add_field(name="Total fame", value=f"**{(player["KillFame"] + player["LifetimeStatistics"]["PvE"]["Total"] + player["LifetimeStatistics"]["Gathering"]["All"]["Total"] + player["LifetimeStatistics"]["Crafting"]["Total"] + player["LifetimeStatistics"]["FishingFame"] + player["LifetimeStatistics"]["FarmingFame"]):,}**", inline=False)

        embed.add_field(name="PvE fame", value=f"**{player["LifetimeStatistics"]["PvE"]["Total"]:,}**")
        embed.add_field(name="Kill fame", value=f"**{player["KillFame"]:,}**")
        embed.add_field(name="Death fame", value=f"**{player["DeathFame"]:,}**")

        for type in ("Fiber", "Hide", "Ore", "Rock", "Wood"):
            embed.add_field(name=f"{type}", value=f"**{player["LifetimeStatistics"]["Gathering"][type]["Total"]:,}**")
        embed.add_field(name="Fishing", value=f"**{player["LifetimeStatistics"]["FishingFame"]:,}**")

        embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text="The data is provided by Sandbox Interactive GmbH.")
        await interaction.response.send_message(embed=embed)


    @command(name="guild", description="Displays detailed information about a guild.")
    @describe(name="The name of the guild you are looking for.")
    @guild_only()
    async def guild(self, interaction: Interaction, name: str) -> None:
        fetcher: SandboxInteractiveInfo = SandboxInteractiveInfo(servers.get_config(cast(Guild, interaction.guild))["fetch_server"])
        guild: Optional[dict[str, Any]] = fetcher.get_guild(name)
        if not guild:
            await interaction.response.send_message(embed=Embed(title=f"{name} doesn't exist",
                                                                color=Color.red(),
                                                                description=f"No guild with name {name} has been "
                                                                "found. Check if you changed the Albion Online  "
                                                                "server or try again later."))
            return

        embed: Embed = Embed(title=f":shield: {guild["guild"]["Name"]}",
                             color=Color.brand_green(),
                             description="Use `/members` to get more information about the "
                             "top 10 guild members.")
        embed.add_field(name=":man: Founder", value=f"**{guild["guild"]["FounderName"]}**")
        if len(guild["guild"]["alliancetag"]) != 0:
            embed.add_field(name=":handshake: Alliance", value=f"**{guild["guild"]["AllianceTag"]}**")
        embed.add_field(name="Members", value=f"**{guild["basic"]["memberCount"]}**")
        embed.add_field(name="Fame", value=f"**{guild["overall"]["fame"]:,}**")
        embed.add_field(name="Kills", value=f"**{guild["overall"]["kills"]:,}**")
        embed.add_field(name="Kill fame", value=f"**{guild["guild"]["killFame"]:,}**")
        embed.add_field(name="Deaths", value=f"**{guild["overall"]["deaths"]:,}**")
        embed.add_field(name="Death fame", value=f"**{guild["guild"]["DeathFame"]:,}**")
        embed.set_author(name=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text="The data is provided by Sandbox Interactive GmbH.")
        await interaction.response.send_message(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Social(bot))
