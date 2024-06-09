#!/usr/bin/env python3
from typing import Any, cast
from discord import Embed, Guild
from discord.ext.commands import BadArgument, Bot, Cog, Context, NoPrivateMessage, command, guild_only
from src import ERROR_COLOR, SUCCESS_COLOR
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
    async def help(self, context: Context) -> None:
        cfg: dict[str, Any] = get_server_config(cast(Guild, context.guild))
        embed = Embed(title=":wave: Hello!",
                      color=SUCCESS_COLOR,
                      description="I'm Bridgewatcher, a Discord bot created by <@692305905123065918>.\n"
                      "I can help you with crafting, refining, trading, and transporting goods all"
                      " arround Albion on all the servers.\n\n"
    
                      "Use `;gold <hours>` or `/gold <hours>` to get recent gold prices on the selected"
                      " server. You can obtain up to 24 prices with this command.\n\n"
    
                      "Use `/price <item_name>` to get the most recent price of an item in different"
                      " in-game markets.\n\n"

                      "If you want to help this project, please install the [Albion Online Data "
                      "Project client](https://albion-online-data.com/) that can fetch the latest"
                      " data from the game.")
        embed.set_author(name="Made by DetectiveKaktus", url="https://github.com/detectivekaktus")
        match cfg["fetch_server"]:
            case 1:
                embed.add_field(name="Currently fetching on :flag_us: American server",
                                value="You can change the fetching server with `;set_server`.")
            case 2:
                embed.add_field(name="Currently fetching on :flag_eu: European server",
                                value="You can change the fetching server with `;set_server`.")
            case 3:
                embed.add_field(name="Currently fetching on :flag_cn: Asian server",
                                value="You can change the fetching server with `;set_server`.")
        await context.send(embed=embed)
