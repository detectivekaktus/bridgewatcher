from discord import Color, Embed, Interaction


class BridgewatcherEmbed(Embed):
    def __init__(
        self,
        interaction: Interaction,
        title: str | None = None,
        color: int | Color | None = None,
        description: str | None = None,
    ):
        super().__init__(title=title, color=color, description=description)
        self.set_author(
            name=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )
