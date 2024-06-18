#!/usr/bin/env python3
from typing import cast
from discord import Color, Embed, Guild
from discord.ext.commands import Bot, Cog, Context, command, guild_only
from src.client import servers


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


class Settings(Cog):
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
    
        servers.update_config(cast(Guild, context.guild), fetch_server)
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
        embed: Embed = Embed(title=f":book: Information about {guild.name}",
                             color=Color.orange(),
                             description=f"There you have a configuration info about {guild.name}.")
        embed.add_field(name="Albion Online server", value=inttostr_server(servers.get_config(cast(Guild, context.guild))["fetch_server"]).capitalize())
        embed.add_field(name="Members of the server", value=guild.member_count)
        embed.add_field(name="Server owner", value=f"<@{guild.owner_id}>")
        await context.send(embed=embed)


    @command(name="help", description="Provides basic information over the bot.")
    async def help(self, context: Context) -> None:
        embed = Embed(title=":wave: Hello!",
                      color=Color.teal(),
                      description="I'm Bridgewatcher, a Discord bot created by <@692305905123065918>.\n"
                      "I can help you with :hammer_pick: crafting, :bricks: refining, :handshake: tradi"
                      "ng, and :truck: transporting goods all around Albion on all the servers.\n\n"

                      "**My commands**\n"
                      "`/info`: get the configuration information\n"
                      "`;set_server`: set the Albion Online server\n"
                      "`/gold`: get price of gold\n"
                      "`/premium`: get price of all types of premium status\n"
                      "`/price`: search for any item price\n"
                      "`/craft:` craft an item and get respective profit\n"
                      "`/flip`: get profit of transporting an item from city to black market\n"
                      "`/utc`: get UTC time.\n"
                      "`/player`: get general information about a player\n"
                      "`/deaths`: get general information about the player's deaths\n"
                      "`/kills`: get general information about the player's kills\n"
                      "`/guild`: get general information about a guild\n"
                      "`/members`: get members of the guild\n\n"
    
                      "**Don't know how to use commands?**\n"
                      "You can find the full list of command by following [this link](https://github.com/d"
                      "etectivekaktus/bridgewatcher).\n\n"

                      "**Found a bug?**\n"
                      "If the bot is behaving in unexpected way :lady_beetle:, please [report it to the developer]"
                      "(https://github.com/detectivekaktus/bridgewatcher/issues/new).")
        embed.set_author(name="Made by DetectiveKaktus", url="https://github.com/detectivekaktus")
        await context.send(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Settings(bot))
