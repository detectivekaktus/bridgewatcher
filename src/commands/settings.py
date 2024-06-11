#!/usr/bin/env python3
from typing import Any, cast
from discord import Embed, Guild
from discord.ext.commands import Bot, Cog, Context, command, guild_only
from src import SUCCESS_COLOR, WHITE
from src.config.config import create_server_config, get_server_config, has_config, update_server_config


def strtoint_server(server: str) -> int:
    match server.lower():
        case "america":
            return 1
        case "europe":
            return 2
        case "asia":
            return 3
        case _:
            return 1


def inttostr_server(server: int) -> str:
    match server:
        case 1:
            return "america"
        case 2:
            return "europe"
        case 3:
            return "asia"
        case _:
            return "america"


class SettingsCog(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command()
    @guild_only()
    async def set_server(self, context: Context, server: str) -> None:
        if server.lower() not in ("america", "europe", "asia"):
            await context.send(f"Unknown server {server}. Please, select a valid server.")
            return

        fetch_server: int = strtoint_server(server.lower())
        if not has_config(cast(Guild, context.guild)):
            create_server_config(cast(Guild, context.guild))
    
        update_server_config(cast(Guild, context.guild), fetch_server)
        match fetch_server:
            case 1:
                await context.send("Server successfully changed to :flag_us: America.")
            case 2:
                await context.send("Server successfully changed to :flag_eu: Europe.")
            case 3:
                await context.send("Server successfully changed to :flag_cn: Asia.")
    

    @command()
    @guild_only()
    async def info(self, context: Context) -> None:
        guild: Guild = cast(Guild, context.guild)
        cfg: dict[str, Any] = get_server_config(guild)
        embed: Embed = Embed(title=f":book: Information about {guild.name}",
                             color=WHITE,
                             description=f"There you have a configuration info about the {guild.name}.")
        embed.add_field(name="Albion Online server", value=inttostr_server(cfg["fetch_server"]).capitalize())
        embed.add_field(name="Members of the server", value=guild.member_count)
        embed.add_field(name="Server owner", value=f"<@{guild.owner_id}>")
        await context.send(embed=embed)


    @command(name="help", description="Provides basic information over the bot.")
    async def help(self, context: Context) -> None:
        embed = Embed(title=":wave: Hello!",
                      color=SUCCESS_COLOR,
                      description="I'm Bridgewatcher, a Discord bot created by <@692305905123065918>.\n"
                      "I can help you with :hammer_pick: crafting, :bricks: refining, :handshake: tradi"
                      "ng, and :truck: transporting goods all around Albion on all the servers.\n\n"
    
                      "You can find the full list of command by following [this link](https://github.com/d"
                      "etectivekaktus/bridgewatcher?tab=readme-ov-file#how-do-i-use-this).\n\n"

                      "If the bot is behaving in unexpected way :lady_beetle:, please report it to the developer.")
        embed.set_author(name="Made by DetectiveKaktus", url="https://github.com/detectivekaktus")
        await context.send(embed=embed)
