from datetime import datetime, timezone

from discord.app_commands import Choice, check, choices, command, describe, guild_only
from discord.ext.commands import Bot, Cog
from discord import Color, Guild, Interaction

from bridgewatcher import __version__
from bridgewatcher.api import AlbionOnlineServers
from bridgewatcher.discord import DETECTIVEKAKTUS_ID
from bridgewatcher.discord.embed import BridgewatcherEmbed
from bridgewatcher.discord.formatting import md
from bridgewatcher.discord.server import ServerManager
from bridgewatcher.discord.views import HelpView


class ExtCog(Cog):
    def __init__(self) -> None:
        super().__init__()

    @command(name="help")
    async def show_help(self, interaction: Interaction) -> None:
        embed = await BridgewatcherEmbed.from_interaction(
            interaction,
            title="👋 Hello!",
            color=Color.teal(),
            description=(
                f"I'm Bridgewatcher, a Discord bot created by <@{DETECTIVEKAKTUS_ID}>.\n"
                "I can help you with 🛠️ crafting, 🧱 refining, 🤝 trading, and "
                "📦 transporting goods 🌐 all around Albion on all the servers.\n\n"
                f"{md.bold("My commands:")}\n"
                "🤖 `/conf`: get my configuration information\n"
                "🌐 `/server`: set Albion Online server\n"
                "🪙 `/gold`: get last 12 gold prices\n"
                "👑 `/premium`: get any premium status price\n"
                "🏷️ `/price`: get any item price\n"
                "🛠️ `/craft`: get profit from crafting an item\n"
                "💹 `/flip`: get profit from market flipping\n"
                "⏰ `/utc`: get UTC time\n"
            ),
        )
        embed.set_author(
            name="Made by DetectiveKaktus", url="https://github.com/detectivekaktus"
        )
        embed.set_footer(text=f"Version: {__version__}")
        embed.add_field(
            name="🐞Found a bug?",
            value=f"You can {md.link("report bugs", "https://github.com/detectivekaktus/bridgewatcher/issues/new?template=bug_report.md")} back to developer on GitHub",
        )

        await interaction.response.send_message(embed=embed, view=HelpView())

    @command(name="utc", description="Shows current UTC time")
    async def show_utc(self, interaction: Interaction) -> None:
        now = datetime.now(timezone.utc)
        await interaction.response.send_message(
            f"Currently it's {md.bold(f"{now.hour}:{now.minute:02d}")} in Albion Online"
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
    await bot.add_cog(ExtCog())
