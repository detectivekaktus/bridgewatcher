#!/usr/bin/env python3
from typing import Any
from discord import Embed
from discord.ext.commands import BadArgument, Bot, Cog, Context, command, guild_only
from src import ERROR, SUCCESS
from src.config.config import create_server_config, get_server_config, has_config, update_server_config


class SettingsCog(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @command()
    @guild_only()
    async def set_server(self, context: Context, server: int) -> None:
        if not context.guild:
            await context.send(embed=Embed(title=":red_circle: Fatal error!",
                                           color=ERROR,
                                           description="This command can be invoked only on a server!"))
            return
    
        if server not in range(1, 4):
            await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                           color=ERROR,
                                           description="Please, specify a valid integer value in range "
                                           "from 1 to 3 for `server` argument."))
            return
    
        if not has_config(context.guild):
            create_server_config(context.guild)
    
        update_server_config(context.guild, server)
        match server:
            case 1:
                await context.send("Server successfully changed to :flag_us: America.")
            case 2:
                await context.send("Server successfully changed to :flag_eu: Europe.")
            case 3:
                await context.send("Server successfully changed to :flag_cn: Asia.")
    
    @set_server.error
    async def raise_set_server_error(self, context: Context, error: Any) -> None:
        if isinstance(error, BadArgument):
            await context.send(embed=Embed(title=":red_circle: Invalid argument!",
                                           color=ERROR,
                                           description="Please, specify a valid integer value in range"
                                           "from 1 to 3 for `server` argument."))
    
    
    @command()
    @guild_only()
    async def help(self, context: Context) -> None:
        if not context.guild:
            await context.send(embed=Embed(title=":red_circle: Fatal error!",
                                           color=ERROR,
                                           description="This command can be invoked only on a server!"))
            return
    
        cfg: dict[str, Any] = get_server_config(context.guild)
        embed = Embed(title=":wave: Hello!",
                      color=SUCCESS,
                      description="I'm Bridgewatcher, a Discord bot created by <@692305905123065918>.\n"
                      "I can help you with crafting, refining, trading, and transporting goods all"
                      " arround Albion on all the servers.\n\n"
    
                      "Use `;gold <hours>` to get recent gold prices on the selected server. You "
                      "can obtain up to 24 prices with this command.\n\n"
    
                      "Use `;price <item_name> <quality> <cities>` to retrieve the price of an item."
                      "The item name is a name required by the Albion Online Project API, the list of "
                      "which you can find [here](https://github.com/ao-data/ao-bin-dumps/blob/master/"
                      "formatted/items.txt). The quality represents the quality level of the item, and"
                      " the cities are the points of sale where you want to get information.\n\n"
    
                      "If you want to help this project, please install the [Albion Online Data "
                      "Project client](https://albion-online-data.com/) that can fetch the latest"
                      " data from the game.")
        embed.set_author(name="Made by DetectiveKaktus", url="https://github.com/detectivekaktus")
        match cfg.get("fetch_server"):
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
