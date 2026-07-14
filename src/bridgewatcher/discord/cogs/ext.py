from datetime import datetime, timezone

from discord.app_commands import Choice, check, choices, command, describe, guild_only
from discord.ext.commands import Bot, Cog
from discord import Guild, Interaction

from bridgewatcher.api import AlbionOnlineServers
from bridgewatcher.discord.util import md, ServerManager


class Ext(Cog):
    def __init__(self) -> None:
        super().__init__()

    @command(name="utc", description="Shows current UTC time")
    async def show_utc(self, interaction: Interaction) -> None:
        now = datetime.now(timezone.utc)
        await interaction.response.send_message(
            f"Currently it's {md.bold(f"{now.hour}:{now.minute}")} in Albion Online"
        )

    @command(name="conf", description="Shows Bridgewatcher configuration")
    @guild_only()
    @check(lambda ctx: ctx.guild is not None)
    async def show_conf(self, interaction: Interaction) -> None:
        guild: Guild = interaction.guild  # type: ignore
        conf = await ServerManager.get_or_create_conf(guild)
        await interaction.response.send_message(
            f"Bridgewatcher is set up for working with {md.bold(conf.fetch_server.capitalize())} server"
        )

    @command(name="server", description="Sets Bridgewatcher working server")
    @describe(server="Albion Online working server")
    @choices(
        server=[Choice(name=server, value=server) for server in AlbionOnlineServers]
    )
    @guild_only()
    @check(lambda ctx: ctx.guild is not None)
    async def set_server(self, interaction: Interaction, server: Choice[str]) -> None:
        guild: Guild = interaction.guild  # type: ignore
        fetch_server = AlbionOnlineServers.from_str(server.value)
        conf = await ServerManager.get_or_update_conf(guild, fetch_server)
        await interaction.response.send_message(
            f"Successfully updated working server to {md.bold(conf.fetch_server.capitalize())}"
        )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Ext())
