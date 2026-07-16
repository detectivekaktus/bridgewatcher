from discord import Color, Embed, Interaction

from bridgewatcher.discord.util import md
from bridgewatcher.discord.util.server import ServerManager


class BridgewatcherEmbed(Embed):
    def __init__(
        self,
        interaction: Interaction,
        title: str | None = None,
        description: str | None = None,
        color: int | Color | None = None,
    ):
        super().__init__(title=title, description=description, color=color)
        self.set_author(
            name=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )

    @staticmethod
    async def from_interaction(
        interaction: Interaction,
        title: str | None = None,
        description: str | None = None,
        color: int | Color | None = None,
    ) -> "BridgewatcherEmbed":
        embed = BridgewatcherEmbed(
            interaction, title=title, description=description, color=color
        )

        if interaction.guild is not None:
            conf = await ServerManager.get_or_create_conf(interaction.guild)
            footer = f"The data is provided by the Albion Online Data Project | {conf.fetch_server.capitalize()} server"
        else:
            footer = "The data is provided by the Albion Online Data Project"
        embed.set_footer(text=footer)

        return embed


class NoItemFoundEmbed(Embed):
    def __init__(self, item_name: str):
        super().__init__(color=Color.red(), title=f"{item_name} does not exist")


class UntrackedItemEmbed(Embed):
    def __init__(self):
        super().__init__(
            color=Color.red(), title=f"This item is not tracked by Bridgewatcher"
        )


class TimeoutEmbed(Embed):
    def __init__(self):
        super().__init__(color=Color.red(), title=f"Your time has run out")
